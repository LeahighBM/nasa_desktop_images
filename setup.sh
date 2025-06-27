#!/bin/bash

echo "Installing python packages"
pip install -r requirements.txt


echo "Creating path ~/Pictures/Wallpapers/NASA/Archived"
mkdir -p ~/Pictures/Wallpapers/NASA/Archived;

echo "Creating CRON to run script"

