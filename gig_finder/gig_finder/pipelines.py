from itemadapter import ItemAdapter
import boto3
import re

class GigFinderPipeline:

    def __init__(self, aws_region, aws_access_key, aws_secret_key):
        self.aws_region = aws_region
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            aws_region=crawler.settings.get("AWS_REGION"),
            aws_access_key=crawler.settings.get("AWS_ACCESS_KEY"),
            aws_secret_key=crawler.settings.get("AWS_SECRET_KEY"),
        )

    def open_spider(self, spider):
        """Initialize the DynamoDB client and create the table if it doesn't exist."""
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key
        )

        # Check if the table exists
        existing_tables = self.dynamodb.meta.client.list_tables()['TableNames']
        if spider.name not in existing_tables:
            # Create the table
            self.dynamodb.create_table(
                TableName=spider.name,
                KeySchema=[
                    {'AttributeName': '_id', 'KeyType': 'HASH'}  # Partition key
                ],
                AttributeDefinitions=[
                    {'AttributeName': '_id', 'AttributeType': 'S'}  # String type
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            # Wait for the table to be created
            table = self.dynamodb.Table(spider.name)
            table.meta.client.get_waiter('table_exists').wait(TableName=spider.name)

        # Initialize the table object
        self.table = self.dynamodb.Table(spider.name)

    def process_item(self, item, spider):
        """Process and save the item to DynamoDB."""
        # Clean strings in the item
        for field in item:
            if isinstance(item[field], str):  # Clean strings
                item[field] = self.clean_string(item[field])
            elif isinstance(item[field], list):  # Clean lists of strings
                item[field] = [self.clean_string(element) for element in item[field] if isinstance(element, str)]

        try:
            spider.logger.info(f"Processing item with _id: {item['_id']}")
            response = self.table.put_item(Item=item)
            spider.logger.info(f"DynamoDB response: {response}")
        except Exception as e:
            spider.logger.error(f"Error inserting item into DynamoDB: {e}")
        return item

    def clean_string(self, text):
        """Clean whitespace and normalize strings."""
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        return text