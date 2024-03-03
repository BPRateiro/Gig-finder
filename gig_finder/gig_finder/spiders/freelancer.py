import scrapy


class FreelancerSpider(scrapy.Spider):
    name = "freelancer"
    allowed_domains = ["www.br.freelancer.com"]
    start_urls = ["https://www.br.freelancer.com/jobs/python/"]

    def parse(self, response):
        """Para cada página listando jobs, extrai os links de cada job"""
        # XPath correspondente à todas as divs que contém a listagem dos jobs
        for job in response.xpath('//div[@class="JobSearchCard-item "]'):
            # Mande visitar cada um dos jobs listados
            yield response.follow(
                job.xpath('.//a/@href').get(), # Link de cada job
                callback=self.parse_job
            )

        # Acessa a próxima página de resultados
        yield response.follow(
            response.xpath('//div[@class="Pagination"]/a[@rel="next"]/@href').get(), 
            callback=self.parse
        )

    def parse_job(self, response):
        """Uma vez na página de detalhes de um job, extrai as informações relevantes"""
        yield {
            'link': response.url,
            'title': response.xpath('//h1/text()').get()
        }