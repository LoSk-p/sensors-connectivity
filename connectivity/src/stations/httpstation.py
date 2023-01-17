# -*- coding: utf-8 -*-
from ctypes import resize
import threading
import time
import json
import cgi
import typing as tp
import logging.config
from http.server import BaseHTTPRequestHandler, HTTPServer
from prometheus_client import Gauge

from .istation import IStation
from ...constants import STATION_VERSION
from ..sensors import EnvironmentalBox

from connectivity.config.logging import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("sensors-connectivity")
thlock = threading.RLock()
sessions = dict()
last_sensors_update = time.time()

ALIVE_SENSORS_METRIC = Gauge(
    "connectivity_sensors_alive_total", "return number of active sessions"
)


class RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, id: str = None) -> None:
        global last_sensors_update
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        updating_sensors_interval = 60 * 60  # 1hr, how often sensors will switch server
        if (time.time() - last_sensors_update) > updating_sensors_interval:
            self.send_header("sensors-count", "0")
            last_sensors_update = time.time()
        else:
            self.send_header("sensors-count", f"{len(sessions)}")
        if id is not None:
            self.send_header("on-server", f"{int(id) in sessions}")
        self.end_headers()

    def do_HEAD(self) -> None:
        self._set_headers()

    def do_GET(self) -> None:
        logger.info(
            "GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers)
        )
        id = self.headers["Sensor-id"]
        self._set_headers(id)
        logger.info(f"HTTP Station session length: {len(sessions)}")

    def do_POST(self) -> None:
        global sessions
        ctype, pdict = cgi.parse_header(self.headers["content-type"])
        length = int(self.headers.get("content-length"))
        d = (
            self.rfile.read(length)
            .decode()
            .replace("SDS_P1", "SDS_pm10")
            .replace("SDS_P2", "SDS_pm25")
        )
        self.data = json.loads(d)
        if "esp8266id" in self.data.keys():
            meas = EnvironmentalBox(self.data)
        with thlock:
            if meas:
                sessions[meas.id] = meas
        self._set_headers()


class HTTP_server(threading.Thread):
    def __init__(self, port: int):
        threading.Thread.__init__(self)
        self.port: int = port

    def run(self) -> None:
        self.server_address = ("", self.port)
        self.httpd = HTTPServer(self.server_address, RequestHandler)
        self.httpd.serve_forever()


class HTTPStation(IStation):
    def __init__(self, config: dict) -> None:
        # super().__init__(config)
        port: int = int(config["httpstation"]["port"])
        self.version = STATION_VERSION
        HTTP_server(port).start()
        self.DEAD_SENSOR_TIME: int = 60 * 60  # 1 hour

    def get_data(self) -> tp.List[dict]:
        global sessions
        global thlock
        result = []
        with thlock:
            stripped = self.drop_dead_sensors(sessions)
            ALIVE_SENSORS_METRIC.set(len(stripped))
        for k, v in stripped.items():
            result.append(v)
        return result
