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
        # yield response.follow(
        #     response.xpath('//div[@class="Pagination"]/a[@rel="next"]/@href').get(), 
        #     callback=self.parse
        # )

    def parse_job(self, response):
        """Uma vez na página de detalhes de um job, extrai as informações relevantes"""
        # Dados em comum:
        common_data = {
            'link': response.url,
            'title': response.xpath('//h1/text()').get(),
        }
        
        # Existem dois templates diferentes para a página de detalhes de um job
        if response.xpath('//fl-text[@class="Project-description"]/div'):
            # O primeiro contém toda descrição em um elemento
            return self.parse_template_1(response, common_data)
        elif response.xpath('//div[@class="PageProjectViewLogout-detail"]/p[not(@class)]'):
            # O segundo contém descrição separada sob vários parágrafos
            return self.parse_template_2(response, common_data)
        else:
            # Caso apareça algum template desconhecido
            self.logger.info('Unknown template for URL: %s', response.url)
    
    def parse_template_1(self, response, common_data):
        """Extrai dados do primeiro template"""
        # Flask Developer for Python UI Creation
        common_data.update({
            'description': response.xpath('//fl-text[@class="Project-description"]/div/text()').get(),
        })
        yield common_data

    def parse_template_2(self, response, common_data):
        """Extrai dados do segundo template"""
        # Golf Club Analysis Application Needed
        common_data.update({ 
            'status': response.xpath('//span[@class="promotion-tag promotion-tag-default"]/text()').get(),
            'price': response.xpath('//p[@class="PageProjectViewLogout-projectInfo-byLine"]/text()').get(),
            'paid_when': response.xpath('//p[@class="PageProjectViewLogout-projectInfo-byLine-paymentInfo"]/text()').get(),
            'posted_when': response.xpath('//span[@class="PageProjectViewLogout-projectInfo-label-deliveryInfo-relativeTime"]/text()').get(),
            'deadline': response.xpath('//span[@class="PageProjectViewLogout-projectInfo-label-deliveryInfo-remainingDays"]/text()').get(),
            'description': response.xpath('//div[@class="PageProjectViewLogout-detail"]/p[not(@class)]/text()').getall(),
        })
        yield common_data