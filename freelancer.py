from typing import Any
import scrapy
from scrapy.http import Response

class FreelancerSpider(scrapy.Spider):
    name = 'freelancer.com'
    start_urls = ['https://www.freelancer.com/jobs/python/'] # Buscando apenas freelances sobre python

    def parse(self, response: Response, **kwargs: Any) -> Any:
        self.log('Testando acesso à freelancer.com \n')
        self.log(response.body)