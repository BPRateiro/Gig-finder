import scrapy
import json
import re

class FreelancerSpider(scrapy.Spider):
    name = 'freelancer'
    start_urls = ['https://www.freelancer.com/job/']
    suffix = "/?status=all" # Show all jobs including closed

    def __init__(self, historical=False, categories=None, *args, **kwargs):
        """Initialize the spider with the historical flag and categories list."""
        super().__init__(*args, **kwargs)
        self.historical = historical if isinstance(historical, bool) else historical.lower() == 'true'

        # Log the raw value of categories for debugging
        self.logger.info(f"Raw categories argument: {categories}, Type: {type(categories)}")

        # Handle JSON decoding for categories argument
        if isinstance(categories, str):
            try:
                self.categories_list = json.loads(categories)
            except json.JSONDecodeError:
                self.logger.error(f"Invalid categories argument: {categories}")
                self.categories_list = []
        else:
            self.categories_list = []

    def parse(self, response):
        """Parse the main page and process job categories."""
        # Extract category data
        category_data = self.extract_categories(response)

        # Process each category one by one
        for category in category_data: 
            category_title = category['category']
            tag_link = category['tag_link']

            if self.categories_list:
                # Ensure category_title is not None and filter correctly
                if not category_title or not any(category_title.startswith(prefix) for prefix in self.categories_list):
                    continue

            # Log the category being processed
            self.logger.info(f"Processing category: {category_title} at {tag_link}")

            # Format links using format_url
            full_link_start = self.format_url(tag_link)
            full_link_finish = self.format_url(tag_link + "20")  # Skip "1X" pages

            # Follow both starting and ending pages
            yield response.follow(full_link_start, callback=self.parse_job_tag)
            yield response.follow(full_link_finish, callback=self.parse_job_tag)

    def extract_categories(self, response):
        """Extract links associated with each category and return as a list of dictionaries."""
        categories = response.xpath('//section[@class="PageJob-category"]')
        category_data = []  # List to store category-tag dictionaries

        for category in categories:
            # Extract category title
            category_title = category.xpath('./header//h3/text()').get()
            if category_title:
                category_title = self.clean_title(category_title)

            # Extract all links and titles within the current category (excluding contests)
            links = category.xpath('.//a[contains(@class, "PageJob-category-link") and not(contains(@href, "contest"))]')
            for link in links:
                tag_title = link.xpath('./@title').get()  # Extract the tag's title
                tag_link = link.xpath('./@href').get()  # Extract the tag's link

                # Append as a dictionary
                if category_title and tag_title and tag_link:
                    category_data.append({
                        "category": category_title,
                        "tag": tag_title.strip(),
                        "tag_link": response.urljoin(tag_link.strip())
                    })

        # Save the extracted category data to a JSON file
        with open('categories.json', 'w', encoding='utf-8') as f:
            json.dump(category_data, f, ensure_ascii=False, indent=4)

        return category_data
    
    def format_url(self, url):
        """Format URL based on historical flag."""
        return url.rstrip('/') + self.suffix if self.historical else url
    
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
                "types": job_card.xpath('.//span[contains(@class, "promotion-tag")]/text()').getall(),
                "verified_payment": bool(job_card.xpath('.//div[contains(@class, "JobSearchCard-primary-heading-status")]')),      
            }

        next_page = response.xpath('//a[@rel="next" and contains(@class, "Pagination-item")]/@href').get()
        if next_page:
            yield response.follow(self.format_url(next_page), callback=self.parse_job_tag)
        else:
            last_page = response.xpath('//a[contains(@class, "Pagination-item") and text()="Last"]/@href').get()
            if last_page:
                yield response.follow(self.format_url(last_page), callback=self.parse_job_tag)