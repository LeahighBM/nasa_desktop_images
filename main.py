import requests
import os
import re
from requests.exceptions import RequestException

NASA_KEY = os.environ.get("NASA_API_KEY")
BASE_URL = f"https://api.nasa.gov/EPIC/api/natural?api_key={NASA_KEY}"

try:
    resp = requests.get(url = BASE_URL)
    resp.raise_for_status()
except RequestException as e:
    print("Error making GET to Baseline URL for image info.", e)

data = resp.json()

image_name = data[0]["image"]
date_time = (data[0]["date"])
ymd = re.findall(r"\d{4}-\d{2}-\d{2}", date_time)
ymd = ymd[0].split("-")
y = ymd[0]
m = ymd[1]
d = ymd[2]

img_url = f"https://api.nasa.gov/EPIC/archive/natural/{y}/{m}/{d}/png/{image_name}.png?api_key={NASA_KEY}" 

file_name = f"{image_name}.png"
try:
    resp = requests.get(img_url, stream=True)
    resp.raise_for_status()

    with open(file_name, "wb") as f:
        print("writing to file")
        for chunk in resp.iter_content():
            f.write(chunk)
    print("Success")

except RequestException as e:
    print("Ran into an error while downloading image", e)
except IOError as e:
    print("Error writing to file", e)