import scrapy


class FreelancerSpider(scrapy.Spider):
    name = "freelancer"
    allowed_domains = ["www.br.freelancer.com"]
    start_urls = ["https://www.br.freelancer.com/jobs/python/?status=all",
                  "https://www.br.freelancer.com/jobs/python/20/?status=all"]

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
        next_page = response.xpath('//div[@class="Pagination"]/a[@rel="next"]/@href').get()
        if next_page is not None:
            print(f"Next page: {next_page}")
            if not next_page.endswith('?status=all'):
                next_page += '/?status=all'  # Append the missing query string
            yield response.follow(next_page, callback=self.parse)

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
        # Exemplo: 'https://www.br.freelancer.com/projects/python/flask-developer-for-python-creation'
        # Muitas informações dentro de um só div: status, posted_when e deadline
        bunched_data = response.xpath('//div[@class="IconTextPair"]//div[@class="NativeElement ng-star-inserted"]//text()').getall()
        common_data.update({
            'id': response.xpath('//app-project-view-logged-out-main/div[1]/fl-text[2]/div/text()').get(),
            'status': bunched_data[0],
            'price': response.xpath('//fl-heading//h2[@class="ng-star-inserted"]/text()').get(),
            'paid_when': response.xpath('//div[1]/div[1]/div[2]/fl-text/div/text()').get(),
            'posted_when': bunched_data[1] + ' ' + bunched_data[2],
            'deadline': bunched_data[-1],
            'description': response.xpath('//fl-text[@class="Project-description"]/div/text()').get(),
            'tags': response.xpath('//fl-tag[@fltrackinglabel="ProjectViewLoggedOut-SkillTag"]//text()').getall(),
        })
        yield common_data

    def parse_template_2(self, response, common_data):
        """Extrai dados do segundo template"""
        # Exemplo: 'https://www.br.freelancer.com/projects/python/golf-club-analysis-application-needed'
        common_data.update({
            'id': response.xpath('//p[@class="PageProjectViewLogout-detail-projectId"]/text()').get(),
            'status': response.xpath('//span[@class="promotion-tag promotion-tag-default"]/text()').get(),
            'price': response.xpath('//p[@class="PageProjectViewLogout-projectInfo-byLine"]/text()').get(),
            'paid_when': response.xpath('//p[@class="PageProjectViewLogout-projectInfo-byLine-paymentInfo"]/text()').get(),
            'posted_when': response.xpath('//span[@class="PageProjectViewLogout-projectInfo-label-deliveryInfo-relativeTime"]/text()').get(),
            'deadline': response.xpath('//span[@class="PageProjectViewLogout-projectInfo-label-deliveryInfo-remainingDays"]/text()').get(),
            'description': response.xpath('//div[@class="PageProjectViewLogout-detail"]/p[not(@class)]/text()').getall(),
            'tags': response.xpath('//a[@class="PageProjectViewLogout-detail-tags-link--highlight"]/text()').getall(),
        })
        yield common_data