import requests
import os
import logging
import subprocess
import random
import sys
import pathlib
from time import sleep
from requests.exceptions import RequestException


# TODO: 
# retry logic on days where there are no images?

# say screw crons?

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

def archive():
    logger.info(f"Archving any existing files into {FILE_PATH}/Archived")

    files = [f for f in os.listdir(FILE_PATH) if os.path.isfile(os.path.join(FILE_PATH, f))]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(FILE_PATH, x)))

    current_wallpaper = files.pop()

    logger.info(f"Archiving files {files}.")
    logger.info(f"Current background detected as {current_wallpaper}; will be ignored.")

    for file in files:
        try:
            os.rename(f"{FILE_PATH}/{file}", f"{FILE_PATH}/Archived/{file}")
            logger.info(f"File {file} successfully archived.")
        except FileNotFoundError as e:
            logger.error("File was not found.", e)


def check_headers(header):
    if int(header["X-Ratelimit-Remaining"])  < MIN_REQ_REMAIN:
        logger.warning(f"X-Ratelimit-Remaining of {header["X-Ratelimit-Remaining"]} "
                       f"is below the configured minimum of {MIN_REQ_REMAIN}.")

def set_wallpaper(img: str):
    logger.info(f"Attempting to set wallpaper to {img}")
    command = f"`gsettings set org.cinnamon.desktop.background picture-uri file://{FILE_PATH}/{img}`"
    logger.info(f"Running command {command}.")
    try:
        subprocess.run(command, shell=True)
    except FileNotFoundError as e:
        logger.error(e)

    logger.info("Wallpaper updated successfully.")   

def main():

    sol = random.randint(1, MAX_SOL)

    if len(sys.argv) != 2:
        print("Usage: `python main.py <minutes to sleep>`")
        print("Program exiting with status 1")
        sys.exit(1)
    
    sec_to_sleep = int(sys.argv[1]) * 60
    logger.info(f"Starting script with sleep time of {sec_to_sleep}s.")

    try:
        logger.info(f"Making request out to api.nasa.gov for image information for sol {sol}")
        resp = requests.get(url = f"{BASE_URL}?sol={sol}&api_key={NASA_KEY}")
        resp.raise_for_status()
        check_headers(resp.headers)
    except RequestException as e:
        logger.error("Error making GET to Baseline URL for image info.", e)

    data = resp.json()

    if len(data["photos"]) == 0:
        logger.warning(f"No images found for Sol {sol}. Program exiting with status 1.")
        # Without cron this will need definite rework
        sys.exit(1)
    
    image_url    = data["photos"][0]["img_src"]
    image_sensor = data["photos"][0]["camera"]["name"]
    image_name   = f"SOL_{data["photos"][0]["sol"]}_{image_sensor}_{data["photos"][0]["id"]}"
    data_type    = data["photos"][0]["img_src"][-3:]
    
    file_name = f"{FILE_PATH}/{image_name}.{data_type}"
    try:
        logger.info(f"Making request to api.nasa.gov for curiosity image from {image_sensor} for SOL {sol}")
        resp = requests.get(image_url, stream=True)
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

    logger.info(f"Sleeping for {sec_to_sleep}s ({sys.argv[1]} mins) before next request.")
    sleep(sec_to_sleep)


if __name__ == "__main__":
    archive()
    while True:
        main()
