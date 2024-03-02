import scrapy


class FreelancerSpider(scrapy.Spider):
    name = "freelancer"
    allowed_domains = ["www.br.freelancer.com"]
    start_urls = ["https://www.br.freelancer.com/jobs/python/"]

    def parse(self, response):
        self.log("Hi, I am a freelancer spider!")
