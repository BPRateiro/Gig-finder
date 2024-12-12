#!/bin/bash

REPO_DIR=/home/ec2-user/Gig-finder
DOCKER_COMPOSE_FILE=$REPO_DIR/docker-compose.yml

# Fetch the latest code
cd $REPO_DIR || exit
git pull origin main

# Build and update the Docker image
docker compose -f $DOCKER_COMPOSE_FILE build

# Run the spider
docker compose -f $DOCKER_COMPOSE_FILE up