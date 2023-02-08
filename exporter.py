#!/usr/bin/env python3

from os import environ
from urllib3 import disable_warnings
from xml.etree.ElementTree import fromstring as xmlfromstring
from re import findall
from requests import get
from requests.exceptions import ConnectionError
from prometheus_client import start_http_server, Gauge
from time import sleep

DESCRIPTIONS = dict(
    config_pending = "is config update pending for this device",
    duty_cycle = "duty cycle limit reached",
    error_code = "current error code",
    low_bat = "battery low",
    operating_voltage = "current battery voltage",
    active_profile = "active thermostat profile",
    actual_temperature = "current temperature",
    boost_mode = "boost mode activated",
    boost_time = "boost timer",
    windows_state = "state of window",
    set_point_temperature = "selected temperature"
)

## disable warning for https if verification fails
if "HOMEMATIC_DISABLE_HTTPS_WARNING" in environ and environ['HOMEMATIC_DISABLE_HTTPS_WARNING']:
    disable_warnings()

if 'HOMEMATIC_CCU_URL' not in environ:
    raise ValueError("HOMEMATIC_CCU_URL environment variable missing")

try:
    VERIFY = not bool(environ['HOMEMATIC_DISABLE_HTTPS_VERIFY'])
except (TypeError, KeyError):
    VERIFY = True

DEVICES = {}
METRICS = {}
SKIP = {
  "HmIP-PS-2": [3,4,5]
}

def debug(msg):
    if "DEBUG" in environ and environ['DEBUG']: 
        print("DEBUG: " + msg)

def convert_metric(metric):
    if metric in ["true","false"]:
        return int(metric == "true")
    return metric

def get_description(name):
    if name in DESCRIPTIONS:
        return DESCRIPTIONS[name]
    else:
        return name

def get_metrics():
    r = get(environ['HOMEMATIC_CCU_URL'] + "/addons/xmlapi/devicelist.cgi", verify = VERIFY)
    xmldata = r.text
    tree = xmlfromstring(xmldata)

    for device in tree:
        device = device.attrib
        if device['device_type'].startswith("HmIP-RCV"):
            continue
        DEVICES[device['ise_id']] = dict(
            name = device['name'],
            type = device['device_type'],
            interface = device['interface']
        )

    r = get(environ['HOMEMATIC_CCU_URL'] + "/addons/xmlapi/statelist.cgi", verify = VERIFY)
    xmldata = r.text
    tree = xmlfromstring(xmldata)
    for device in tree:
        ise_id = device.attrib['ise_id']
        if ise_id not in DEVICES:
            continue
        dev = DEVICES[ise_id]
        debug(device.attrib['name'])
        for channel in device:
            if dev['type'] in SKIP and int(channel.attrib['index']) in SKIP[dev['type']]:
                continue
            debug("- " + channel.attrib['name'])
            for datapoint in channel:
                metric_name = findall("^.*\.([A-Z_]+)$", datapoint.attrib['name'])[0].lower()
                metric_value = convert_metric(datapoint.attrib['value'])

                if metric_value == "":
                    continue
                debug("-- " + datapoint.attrib['name'] + ": " + str(metric_value))

                if metric_name not in METRICS:
                    METRICS[metric_name] = Gauge("homematic_" + metric_name, get_description(metric_name), ["device_name","device_type","device_interface"])
                try:
                    METRICS[metric_name].labels(**dict(
                        device_type = dev['type'],
                        device_interface = dev['interface'],
                        device_name = dev['name']
                    )).set(metric_value)
                except ValueError:
                    pass

def loop(interval):
    while True:
        try:
            debug("starting loop run")
            get_metrics()
            debug(f"sleeping for {interval}s")
            sleep(interval)
        except ConnectionError as err:
            debug(f"connection error: {err}")
            debug(f"sleeping {interval}s and retrying...")
            sleep(interval)

if __name__ == '__main__':
    try:
        debug(f"trying to start server on port {environ['HOMEMATIC_EXPORTER_PORT']}")
        start_http_server(environ['HOMEMATIC_EXPORTER_PORT'])
    except KeyError:
        debug("trying to start server on port 8999")
        start_http_server(8999)

    try:
        debug(f"starting loop with interval {environ['HOMEMATIC_POLL_INTERVAL']}s")
        loop(int(environ['HOMEMATIC_POLL_INTERVAL']))
    except KeyError:
        debug("starting loop with interval 30s")
        loop(30)
