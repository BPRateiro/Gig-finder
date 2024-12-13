import datetime
import boto3
import re

from boto3.dynamodb.conditions import Attr
from decimal import Decimal

class GigFinderPipeline:
    def __init__(self, aws_region, aws_access_key, aws_secret_key):
        self.dynamodb_manager = DynamoDBManager(aws_region, aws_access_key, aws_secret_key)
        self.track_fields = ["status", "price_min", "price_max", "offers", "is_competition", 
                             "is_hourly", "types", "verified_payment", "tags"]  # Default fields to track

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            aws_region=crawler.settings.get("AWS_REGION"),
            aws_access_key=crawler.settings.get("AWS_ACCESS_KEY"),
            aws_secret_key=crawler.settings.get("AWS_SECRET_KEY"),
        )

    def open_spider(self, spider):
        """Initialize the DynamoDB manager and table."""
        self.table = self.dynamodb_manager.get_or_create_table(spider.name)

    def close_spider(self, spider):
        """Mark offers as ended if they are not seen today and don't have the status 'Ended'."""
        today = datetime.datetime.now(datetime.timezone.utc).date()
        
        # Fetch items where the status is not 'Ended'
        active_items = self.dynamodb_manager.get_items_excluding_status(self.table, "Ended", ["_id", "last_seen_at", "status"])

        for item in active_items:
            last_seen_date = datetime.datetime.fromisoformat(item['last_seen_at']).date()
            if last_seen_date < today:
                previous_status = item['status']
                success = self.dynamodb_manager.update_status_to_ended(
                    table=self.table,
                    item_id=item['_id'],
                    previous_status=previous_status
                )
                if success:
                    spider.logger.info(f"Marked item {item['_id']} as Ended.")
                else:
                    spider.logger.error(f"Failed to update item {item['_id']} to Ended.")

    def process_item(self, item, spider):
        """Process and save the item to DynamoDB."""
        # Remove private projects and records without price
        if (item.get('offers') is None and item.get('price') is None) or item.get('price') == 'N/A':
            spider.logger.info(f"Skipping private project or item with no price: {item.get('_id')}")
            return None
        
        # Clean strings in the item
        for field in item:
            if isinstance(item[field], str):  # Clean strings
                item[field] = self.clean_string(item[field])
            elif isinstance(item[field], list):  # Clean lists of strings
                item[field] = [self.clean_string(element) for element in item[field] if isinstance(element, str)]

        # Mark if the job is part of a competition
        item['is_competition'] = bool(re.search(r'entries', str(item.get('offers', ''))))

        # Extract the number of offers
        offers_match = re.search(r'(\d+)', str(item.get('offers', '')))
        item['offers'] = int(offers_match.group(1)) if offers_match else None

        # Add the is_hourly column
        hourly_suffix = r'\s*/\s*hr'
        item['is_hourly'] = bool(re.search(hourly_suffix, str(item.get('price', ''))))

        # Extract price_min and price_max
        extraction_pattern = r'\$(\d+)(?:\s*-\s*\$(\d+))?'
        extracted = re.search(extraction_pattern, item.get("price"))
        item['price_min'] = Decimal(extracted.group(1)) if extracted else None
        item['price_max'] = Decimal(extracted.group(2)) if extracted and extracted.group(2) else item['price_min']
        item.pop('price', None) # Drop the original price column

        # Append site prefix to the _id
        item['_id'] = f"https://www.freelancer.com{item.get('_id', '')}"

        # Update last_seen_at timestamp
        item['last_seen_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            item = self.prepare_item_with_history(item)  # Check for changes
            self.dynamodb_manager.insert_item(self.table, item)
        except Exception as e:
            spider.logger.error(f"Error inserting item into DynamoDB: {e}")
        return item
    
    def prepare_item_with_history(self, item):
        """Prepare the item by adding history tracking for selected fields."""
        existing_item = self.dynamodb_manager.get_item_with_projection(self.table, item['_id'], self.track_fields + ["history"])
        if existing_item:
            diff = self.calculate_diff(existing_item, item)
            history = existing_item.get('history', [])
            if diff:  # Only update if there are changes
                change_record = {
                    "modified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "changes": diff
                }
                history.append(change_record)
            item['created_at'] = existing_item.get('created_at')
            item['history'] = history
        else:  # First insertion
            item['created_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            item['history'] = []
        return item

    def clean_string(self, text):
        """Clean whitespace and normalize strings."""
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    def calculate_diff(self, old_item, new_item):
        """Calculate the diff for tracked fields."""
        diff = {}
        for field in self.track_fields:
            if field in new_item and (field not in old_item or old_item[field] != new_item[field]):
                diff[field] = old_item.get(field)
        return diff


class DynamoDBManager:
    def __init__(self, aws_region, aws_access_key, aws_secret_key):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )

    def get_or_create_table(self, table_name, partition_key='_id', partition_key_type='S'):
        """Ensure the table exists or create it if it doesn't."""
        existing_tables = self.dynamodb.meta.client.list_tables()['TableNames']
        if table_name not in existing_tables: # Create the table
            self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': partition_key, 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': partition_key, 'AttributeType': partition_key_type}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table = self.dynamodb.Table(table_name) # Wait for the table to be created
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        else:
            table = self.dynamodb.Table(table_name)
        return table

    def insert_item(self, table, item):
        """Insert an item into the given DynamoDB table."""
        try:
            return table.put_item(Item=item)
        except Exception as e:
            raise RuntimeError(f"Failed to insert item into table: {e}")

    def get_item_with_projection(self, table, partition_key_value, fields):
        """Retrieve an item with only specific fields."""
        try:
            # Map fields to handle reserved keywords
            expression_attribute_names = {f"#{field}": field for field in fields}
            projection_expression = ", ".join(expression_attribute_names.keys())

            response = table.get_item(
                Key={'_id': partition_key_value},
                ProjectionExpression=projection_expression,
                ExpressionAttributeNames=expression_attribute_names
            )
            return response.get('Item')
        except Exception as e:
            raise RuntimeError(f"Failed to get item with projection from table: {e}")
        
    def update_status_to_ended(self, table, item_id, previous_status):
        """Update the status of an item to 'Ended' and append to its history."""
        try:
            table.update_item(
                Key={'_id': item_id},
                UpdateExpression="""
                    SET #status = :new_status,
                        #history = list_append(if_not_exists(#history, :empty_list), :new_history)
                """,
                ConditionExpression="attribute_exists(#_id) AND #status <> :new_status",
                ExpressionAttributeNames={
                    "#_id": "_id",
                    "#status": "status",
                    "#history": "history"
                },
                ExpressionAttributeValues={
                    ":new_status": "Ended",
                    ":new_history": [{
                        "modified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "changes": {"status": previous_status}
                    }],
                    ":empty_list": []
                }
            )
            return True
        except Exception as e:
            print(f"Error updating item {item_id} to Ended: {e}")
            return False

    def get_items_excluding_status(self, table, excluded_status, fields=None):
        """Retrieve all items that do not have the specified excluded status, with optional field projection."""
        try:
            items = []
            scan_kwargs = {"FilterExpression": Attr('status').ne(excluded_status)}

            if fields:
                # Map fields to handle reserved keywords
                expression_attribute_names = {f"#{field}": field for field in fields}
                projection_expression = ", ".join(expression_attribute_names.keys())
                scan_kwargs.update({
                    "ProjectionExpression": projection_expression,
                    "ExpressionAttributeNames": expression_attribute_names,
                })

            response = table.scan(**scan_kwargs)
            items.extend(response.get('Items', []))

            # Continue scanning if more results exist
            while 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = table.scan(**scan_kwargs)
                items.extend(response.get('Items', []))

            return items
        except Exception as e:
            raise RuntimeError(f"Failed to scan table for items excluding status '{excluded_status}': {e}")
