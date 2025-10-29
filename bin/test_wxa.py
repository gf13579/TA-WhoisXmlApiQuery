import os
import sys
import time
import datetime
import requests
import json
import logging
import time
import wxa
import sys

def test():
    api_key = os.environ['API_KEY']
    domains = ["splunk.com","intalock.com.au"]
    x = wxa.submit_queries(api_key, domains)    
    print(x)

test()

