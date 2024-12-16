#!/bin/bash

# Run the update script
./update.sh

# Run the spider for specific categories without historical data
docker compose -f /home/ec2-user/Gig-finder/docker-compose.yml run gig_finder \
    scrapy crawl freelancer -a categories='[\"Websites\", \"Data\", \"Artificial\"]' -a historical=True