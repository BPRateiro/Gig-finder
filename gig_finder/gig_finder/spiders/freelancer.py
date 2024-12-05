import scrapy
import json
import re

class FreelancerSpider(scrapy.Spider):
    name = 'freelancer'
    start_urls = ['https://www.freelancer.com/job/']
    suffix = "/?status=all" # Show all jobs including closed

    def __init__(self, historical=False, *args, **kwargs):
        """Initialize the spider with the historical flag."""
        super().__init__(*args, **kwargs)
        self.historical = historical if isinstance(historical, bool) else historical.lower() == 'true'

    def parse(self, response):
        """Extract links associated with each category"""
        categories = response.xpath('//section[@class="PageJob-category"]')
        category_links = {} # Dictionary to store categories and their associated links

        for category in categories:
            # Extract category title
            category_title = category.xpath('./header//h3/text()').get()
            if category_title:
                category_title = category_title.strip()

            # Extract all links within the current category (excluding contests)
            links = category.xpath('.//a[contains(@class, "PageJob-category-link") and not(contains(@href, "contest"))]/@href').getall()

            # Store the links associated with the category
            if category_title and links:
                category_links[self.clean_title(category_title)] = [response.urljoin(link) for link in links]

            # Save category links to a JSON file
            with open('categories.json', 'w', encoding='utf-8') as f:
                json.dump(category_links, f, ensure_ascii=False, indent=4)

        # for category in categories[1:2]:
        #     # Extract category title
        #     category_title = category.xpath('./header//h3/text()').get()
        #     if category_title:
        #         category_title = self.clean_title(category_title)

        #     # Extract all job links within the current category excluding contests
        #     links = category.xpath('.//a[contains(@class, "PageJob-category-link") and not(contains(@href, "contest"))]/@href').getall()

        #     # Log the category being processed
        #     self.logger.info(f"Processing category: {category_title} with {len(links)} links")

        #     for link in links[:1]:
        #         if self.historical: # Get all data
        #             full_link_start = response.urljoin(link.rstrip('/')) + self.suffix
        #             full_link_finish = response.urljoin(link) + "20" + self.suffix # Skip the 1X pages, because they only redirect to start
        #         else: # Fetch only open jobs
        #             full_link_start = response.urljoin(link.rstrip('/'))
        #             full_link_finish = response.urljoin(link) + "20" # Skip the 1X pages, because they only redirect to start

        #         yield response.follow(full_link_start, callback=self.parse_job_tag)
        #         yield response.follow(full_link_finish, callback=self.parse_job_tag)
    
    def clean_title(self, title):
        """Clean a title by removing extra whitespace and numbers in parentheses."""
        title = title.strip()  # Remove leading and trailing whitespace
        title = re.sub(r'\s*\(\d+\)$', '', title)  # Remove numbers in parentheses
        return title if title else None  # Return None for empty titles

    def parse_job_tag(self, response):
        """Extract all job cards"""
        job_cards = response.xpath('//div[contains(@class, "JobSearchCard-item-inner")]')
        
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

        # Check for the "next" page link
        next_page = response.xpath('//a[@rel="next" and contains(@class, "Pagination-item")]/@href').get()
        
        if next_page:
            # Use historical logic for "next" link
            next_page = next_page.rstrip('/') + self.suffix if self.historical else next_page
            yield response.follow(next_page, callback=self.parse_job_tag)
        else:
            # If "next" is not available, fetch the "last" page link
            last_page = response.xpath('//a[contains(@class, "Pagination-item") and text()="Last"]/@href').get()
            if last_page:
                last_page = last_page.rstrip('/') + self.suffix if self.historical else last_page
                yield response.follow(last_page, callback=self.parse_job_tag)