#!/bin/bash

# Set repository and Docker Compose file paths
REPO_DIR=/home/ec2-user/Gig-finder
DOCKER_COMPOSE_FILE=$REPO_DIR/docker-compose.yml

# Fetch the latest code
cd $REPO_DIR || exit
/usr/bin/git fetch origin main
/usr/bin/git reset --hard origin/main

# Build and update the Docker image
/usr/local/bin/docker-compose -f $DOCKER_COMPOSE_FILE build