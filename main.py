import requests
import os
import re
import logging
import subprocess
import random
import sys
import pathlib
from enum import Enum
from requests.exceptions import RequestException


# TODO: 
# Figure out what api we want to pull from to start. 
#   EPIC was good PoC but does not update frequently
#   Thought: Could do landsat and pull random lat longs from the API 
#       with each pull. Do every 60-90 mins?

# Write bash script to set up crontab as well as commands for 
#   setting up directory structure for wallpapers (partially complete)

# ~~Introduce logging~~
# Re work archive flow to prevent black screen from appearing 
#   before image is downloaded and set

# retry logic on days where there are no images?

NASA_KEY = os.environ.get("NASA_API_KEY")
BASE_URL = f"https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos"
FILE_PATH = os.path.expanduser("~/Pictures/Wallpapers/NASA")
MIN_REQ_REMAIN = 2000
MAX_SOL = 4500

path = pathlib.Path(__file__).resolve().parent


logging.basicConfig(
    filename=f"{path}/logs.log",
    level=logging.INFO,
    format= '%(asctime)s.%(msecs)03d: %(levelname)s | %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def check_headers(header):
    if int(header["X-Ratelimit-Remaining"])  < MIN_REQ_REMAIN:
        logger.warning(f"X-Ratelimit-Remaining of {header["X-Ratelimit-Remaining"]} "
                       f"is below the configured minimum of {MIN_REQ_REMAIN}.")

def set_wallpaper(img: str):
    logger.info(f"Attempting to set wallpaper to {img}")
    command = f"gsettings set org.cinnamon.desktop.background picture-uri file://{FILE_PATH}/{img}"
    logger.info(f"Running command {command}.")
    try:
        subprocess.run(command, shell=True)
    except FileNotFoundError as e:
        logger.error(e)
        

def main():

    sol = random.randint(1,MAX_SOL)
    try:
        logger.info(f"Making request out to api.nasa.gov for image information for sol {sol}")
        resp = requests.get(url = f"{BASE_URL}?sol={sol}&api_key={NASA_KEY}")
        # check_headers(resp.headers)
        resp.raise_for_status()
    except RequestException as e:
        logger.error("Error making GET to Baseline URL for image info.", e)

    data = resp.json()

    if len(data["photos"]) == 0:
        logger.warning(f"No images found for Sol {sol}. Program exiting with status 1.")
        sys.exit(1)
    
    image_url = data["photos"][0]["img_src"]
    image_sensor = data["photos"][0]["camera"]["name"]
    image_name = f"SOL_{data["photos"][0]["sol"]}_{image_sensor}_{data["photos"][0]["id"]}"
    data_type = data["photos"][0]["img_src"][-3:]
    
    file_name = f"{FILE_PATH}/{image_name}.{data_type}"
    try:
        logger.info(f"Making request to api.nasa.gov for curiosity image from {image_sensor} for SOL {sol}")
        resp = requests.get(image_url, stream=True)
        # check_headers(resp.headers)
        resp.raise_for_status()

        with open(file_name, "wb") as f:
            logger.info(f"Writing to file {file_name}")
            for chunk in resp.iter_content():
                f.write(chunk)
        logger.info("File write was successful.")

    except RequestException as e:
        logger.error("Ran into an error while downloading image", e)
    except IOError as e:
        logger.error("Error writing to file", e)

    set_wallpaper(img=f"{image_name}.{data_type}")

def archive():
    logger.info(f"Archving any existing files into {FILE_PATH}/Archived")
    files = [f for f in os.listdir(FILE_PATH) if os.path.isfile(os.path.join(FILE_PATH, f))]

    for file in files:
        try:
            os.rename(f"{FILE_PATH}/{file}", f"{FILE_PATH}/Archived/{file}")
            logger.info(f"File {file} successfully archived.")
        except FileNotFoundError as e:
            logger.error("File was not found.", e)


if __name__ == "__main__":
    # archive()
    main()
