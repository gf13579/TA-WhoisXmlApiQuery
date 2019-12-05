import os
import sys
import time
import datetime
import requests
import json
import logging
import time
import wxa

def test():
    api_key = "at_wl9FLGub0XShvCEzJgajDpPV9JyeI"
    domains = ["180.189.154.30"]
    results = wxa.get_whois_info(api_key, domains)
    print(results)

test()
