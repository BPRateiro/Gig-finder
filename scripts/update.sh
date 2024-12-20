#!/bin/bash

# Set repository and Docker Compose file paths
REPO_DIR=/home/ec2-user/Gig-finder
DOCKER_COMPOSE_FILE=$REPO_DIR/docker-compose.yml

# Fetch the latest code
cd $REPO_DIR || exit
git fetch origin main
git reset --hard origin/main

# Build and update the Docker image
docker-compose -f $DOCKER_COMPOSE_FILE build