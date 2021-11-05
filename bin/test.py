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
    api_key = input("Enter your API key:")
    domains = ["splunk.com","intalock.com.au"]
    #for d in domains:
    #    result = wxa.submit_query_single(api_key, d)
    #    print(result)
    x = wxa.submit_queries(api_key, domains)    
    print(x)
#print(results)

test()

