import random
import requests, json
import time
import logging.config
from config.logging import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

id = 1

header = {"Content-type": "application/json"}



while id < 102000:

    #id_b = f'{id + 1}'
    pm10 = round(random.uniform(0.1, 100.99), 3)
    pm25 = round(random.uniform(0.1, 100.99), 3)
    lat = round(random.uniform(0.000000, 60.000000), 6)
    lon = round(random.uniform(0.000000, 49.999999), 6)
    body = {
      "esp8266id": id,
      "software_version": "NRZ-2020-129",
      "sensordatavalues": [
        {
        "value_type": "SDS_P1",
        "value": pm10
        },
        {
        "value_type": "SDS_P2",
        "value": pm25
        },
        {
          "value_type": "temperature",
          "value": "22.93"
        },
        {
          "value_type": "humidity",
          "value": "39.44"
        },
        {
        "value_type": "samples",
        "value": "890618"
        },
        {
        "value_type": "min_micro",
        "value": "43"
        },
        {
        "value_type": "max_micro",
        "value": "21069"
        },
        {
        "value_type": "GPS_lat",
        "value": lat
        },
        {
        "value_type": "GPS_lon",
        "value": lon
        },
        {
        "value_type": "signal",
        "value": "-46"
        }
      ]
    }
    try:
      response = requests.post('http://connectivity.robonomics.network :65/', data=json.dumps(body), headers=header)
      id += 1
    except Exception as e:
      logger.warning(e)
      pass
    time.sleep(20)