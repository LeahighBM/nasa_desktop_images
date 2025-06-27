import requests
import os
import re
import logging
import subprocess
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

NASA_KEY = os.environ.get("NASA_API_KEY")
BASE_URL = f"https://api.nasa.gov/EPIC/api/natural?api_key={NASA_KEY}"
FILE_PATH = os.path.expanduser("~/Pictures/Wallpapers/NASA")
MIN_REQ_REMAIN = 2000

logging.basicConfig(
    filename="logs.log",
    level=logging.INFO,
    format= '%(asctime)s.%(msecs)03d: %(levelname)s | %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def check_headers(header):
    if int(header["X-Ratelimit-Remaining"])  < MIN_REQ_REMAIN:
        logger.warning(f"X-Ratelimit-Remaining of {header["X-Ratelimit-Remaining"]}"
                       f"is below the configured minimum of {MIN_REQ_REMAIN}.")

def set_wallpaper(img: str):
    logger.info(f"Attempting to set wallpaper to {img}")
    command = f"gsettings set org.cinnamon.desktop.background picture-uri file://{FILE_PATH}/{img}"
    logger.info(f"Running command {command}.")
    try:
        subprocess.run(command, shell=True)
    except FileNotFoundError as e:
        # logger.error(e)
        print(e)

def fetch_and_store():

    try:
        logger.info("Making request out to api.nasa.gov for image information")
        resp = requests.get(url = BASE_URL)
        check_headers(resp.headers)
        resp.raise_for_status()
    except RequestException as e:
        print("Error making GET to Baseline URL for image info.", e)
        logger.error("Error making GET to Baseline URL for image info.", e)

    data = resp.json()

    image_name = data[0]["image"]
    date_time = (data[0]["date"])
    ymd = re.findall(r"\d{4}-\d{2}-\d{2}", date_time)
    ymd = ymd[0].split("-")
    y = ymd[0]
    m = ymd[1]
    d = ymd[2]

    img_url = f"https://api.nasa.gov/EPIC/archive/natural/{y}/{m}/{d}/png/{image_name}.png?api_key={NASA_KEY}" 

    file_name = f"{FILE_PATH}/{image_name}.png"
    try:
        logger.info(f"Making request to api.nasa.gov for image {image_name} from date {y}/{m}/{d}")
        resp = requests.get(img_url, stream=True)
        check_headers(resp.headers)
        resp.raise_for_status()

        with open(file_name, "wb") as f:
            print("writing to file")
            logger.info(f"Writing to file {file_name}")
            for chunk in resp.iter_content():
                f.write(chunk)
        print("Success")
        logger.info("File write was successful.")

    except RequestException as e:
        print("Ran into an error while downloading image", e)
        logger.error("Ran into an error while downloading image", e)
    except IOError as e:
        print("Error writing to file", e)
        logger.error("Error writing to file", e)

    # print(image_name)
    set_wallpaper(img=f"{image_name}.png")

def archive():
    logger.info(f"Archving any existing files into {FILE_PATH}/Archived")
    files = [f for f in os.listdir(FILE_PATH) if os.path.isfile(os.path.join(FILE_PATH, f))]

    for file in files:
        try:
            os.rename(f"{FILE_PATH}/{file}", f"{FILE_PATH}/Archived/{file}")
            logger.info(f"File {file} successfully archived.")
        except FileNotFoundError as e:
            print("File was not found.", e)
            logger.error("File was not found.", e)


if __name__ == "__main__":
    archive()
    fetch_and_store()
