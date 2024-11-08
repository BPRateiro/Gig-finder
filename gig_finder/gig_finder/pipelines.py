# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymongo
import re

class GigFinderPipeline:

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get("MONGO_URI"),
            mongo_db=crawler.settings.get("MONGO_DATABASE", "items"),
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.collection_name = spider.name

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        """Tira os caracteres de espaço em branco do início e do fim de cada string"""
        for field in item:
            if isinstance(item[field], str): # Caso seja uma string
                item[field] = self.clean_string(item[field])
            elif isinstance(item[field], list): # Caso seja uma lista de strings
                item[field] = [self.clean_string(element) for element in item[field] if isinstance(element, str)]
        # Use `update_one` with `upsert=True` to insert or update the document based on `_id`
        self.db[self.collection_name].update_one(
            {"_id": item["_id"]},    # Match by `_id`
            {"$set": item},          # Update with new item data
            upsert=True              # Insert if no document with `_id` exists
        )
        return item
    
    def clean_string(self, text):
        """Tira os caracteres de espaço em branco do início e do fim de cada string"""
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        return text