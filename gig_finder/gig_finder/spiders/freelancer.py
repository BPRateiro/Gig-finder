import scrapy
import json
import re

class FreelancerSpider(scrapy.Spider):
    name = 'freelancer'
    start_urls = ['https://www.freelancer.com/job/']
    suffix = "/?status=all" # Show all jobs including closed

    def parse(self, response):
        """Extract links associated with the "Websites, IT" section"""
        links = response.xpath('//section[contains(header//h3/text(), "Websites, IT")]/ul/li/a/@href').getall()

        titles = response.xpath('//section[contains(header//h3/text(), "Websites, IT")]/ul/li/a/text()').getall()
        cleaned_titles = [
            cleaned_title
            for title in titles
            if (cleaned_title := self.clean_title(title))  # Clean once and filter
        ]
        with open('categories.json', 'w', encoding='utf-8') as f:
            json.dump(cleaned_titles, f, ensure_ascii=False, indent=4)

        for link in links:
            full_link_start = response.urljoin(link.rstrip('/')) + self.suffix # Starting position
            full_link_finish = response.urljoin(link) + "20" + self.suffix # Skip the 1X pages, because they only redirect to start

            yield response.follow(full_link_start, callback=self.parse_job_category)
            yield response.follow(full_link_finish, callback=self.parse_job_category)
    
    def clean_title(self, title):
        """Clean a title by removing extra whitespace and numbers in parentheses."""
        title = title.strip()  # Remove leading and trailing whitespace
        title = re.sub(r'\s*\(\d+\)$', '', title)  # Remove numbers in parentheses
        return title if title else None  # Return None for empty titles

    def parse_job_category(self, response):
        """Extract all div elements with a class that contains "JobSearchCard-item"""
        job_cards = response.xpath('//div[contains(@class, "JobSearchCard-item")]')
        
        for job_card in job_cards:
            yield {
                "_id": job_card.xpath('.//a[contains(@class, "JobSearchCard-primary-heading-link")]/@href').get(),
                "title": job_card.xpath('.//a[contains(@class, "JobSearchCard-primary-heading-link")]/text()').get(),
                "description": job_card.xpath('.//p[contains(@class, "JobSearchCard-primary-description")]/text()').get(),
                "status": job_card.xpath('.//span[contains(@class, "JobSearchCard-primary-heading-days")]/text()').get(),
                "tag_links": job_card.xpath('.//a[contains(@class, "JobSearchCard-primary-tagsLink")]/@href').getall(),
                "tags": job_card.xpath('.//a[contains(@class, "JobSearchCard-primary-tagsLink")]/text()').getall(),
                "price": job_card.xpath('.//div[contains(@class, "JobSearchCard-primary-price")]/text()').get(),
                "offers": job_card.xpath('.//div[contains(@class, "JobSearchCard-secondary-entry")]/text()').get(),            
            }

        next_page = response.xpath('//a[@rel="next" and contains(@class, "Pagination-item")]/@href').get()
        if next_page:
            yield response.follow(next_page + self.suffix, callback=self.parse_job_category)