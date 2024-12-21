#!/bin/bash

# Run the update script
/home/ec2-user/Gig-finder/scripts/update.sh

# Run the spider for specific categories without historical data
/usr/local/bin/docker-compose -f /home/ec2-user/Gig-finder/docker-compose.yml run gig_finder \
    scrapy crawl freelancer -a categories='["Websites", "Data", "Artificial"]' -a historical=False