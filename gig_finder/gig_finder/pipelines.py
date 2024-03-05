# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re


class GigFinderPipeline:
    def process_item(self, item, spider):
        """Tira os caracteres de espaço em branco do início e do fim de cada string"""
        for field in item:
            if isinstance(item[field], str): # Caso seja uma string
                item[field] = self.clean_string(item[field])
            elif isinstance(item[field], list): # Caso seja uma lista de strings
                item[field] = [self.clean_string(element) for element in item[field] if isinstance(element, str)]
        return item
    
    def clean_string(self, text):
        """Tira os caracteres de espaço em branco do início e do fim de cada string"""
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        return text
