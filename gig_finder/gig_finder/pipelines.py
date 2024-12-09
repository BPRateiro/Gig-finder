import boto3
import re

class GigFinderPipeline:
    def __init__(self, aws_region, aws_access_key, aws_secret_key):
        self.dynamodb_manager = DynamoDBManager(aws_region, aws_access_key, aws_secret_key)

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

    def process_item(self, item, spider):
        """Process and save the item to DynamoDB."""
        # Clean strings in the item
        for field in item:
            if isinstance(item[field], str):  # Clean strings
                item[field] = self.clean_string(item[field])
            elif isinstance(item[field], list):  # Clean lists of strings
                item[field] = [self.clean_string(element) for element in item[field] if isinstance(element, str)]

        try:
            self.dynamodb_manager.insert_item(self.table, item)
        except Exception as e:
            spider.logger.error(f"Error inserting item into DynamoDB: {e}")
        return item

    def clean_string(self, text):
        """Clean whitespace and normalize strings."""
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    

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
        if table_name not in existing_tables:
            # Create the table
            self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': partition_key, 'KeyType': 'HASH'}  # Partition key
                ],
                AttributeDefinitions=[
                    {'AttributeName': partition_key, 'AttributeType': partition_key_type}  # Attribute type
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            # Wait for the table to be created
            table = self.dynamodb.Table(table_name)
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        else:
            table = self.dynamodb.Table(table_name)
        return table

    def insert_item(self, table, item):
        """Insert an item into the given DynamoDB table."""
        return table.put_item(Item=item)