#!/bin/bash

# Set repository and Docker Compose file paths
REPO_DIR=/home/ec2-user/Gig-finder
DOCKER_COMPOSE_FILE=$REPO_DIR/docker-compose.yml

# Fetch the latest code
cd $REPO_DIR || exit
/usr/bin/git fetch origin main
/usr/bin/git reset --hard origin/main

# Stop any running services and remove orphaned containers
/usr/local/bin/docker-compose -f $DOCKER_COMPOSE_FILE down --remove-orphans

# Remove unused Docker resources to free up space
/usr/local/bin/docker system prune -f --volumes

# Build and update the Docker image
/usr/local/bin/docker-compose -f $DOCKER_COMPOSE_FILE build