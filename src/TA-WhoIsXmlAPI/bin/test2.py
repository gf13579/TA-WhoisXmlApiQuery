import os
import sys
import time
import datetime
import requests
import json
import logging
import time

def submit_query(api_key,domains):
    retDict = {}
    for d in domains:
        new_rec = submit_query_single(api_key,d)
        retDict[j['WhoIsRecord']['domainName']] = new_rec
    
    return retDict


def submit_query_single(api_key, domain):
    url = 'https://www.whoisxmlapi.com/whoisserver/WhoisService?' + 'domainName=' + domain + '&apiKey=' + api_key + "&outputFormat=JSON"

    response = requests.get(url)

    #print(urlopen(url).read().decode('utf8'))

    rec = json.loads(response.content)

    new_rec = {}
    try:
        new_rec['contactEmail'] = rec.get('WhoisRecord').get('contactEmail')
        new_rec['registrarName'] = rec.get('WhoisRecord').get('registrarName')
        new_rec['organization'] = rec.get('WhoisRecord').get('registryData').get('registrant').get('organization')
        new_rec['registrantName'] = rec.get('WhoisRecord').get('registryData').get('registrant').get('name')
        new_rec['techContactName'] = rec.get('WhoisRecord').get('registryData').get('technicalContact').get('name')
        new_rec['street1'] = rec.get('WhoisRecord').get('registryData').get('registrant').get('street1')
        new_rec['postalCode'] = rec.get('WhoisRecord').get('registryData').get('registrant').get('postalCode')
    except:
        pass

    return new_rec


def test():
    api_key = "at_wl9FLGub0XShvCEzJgajDpPV9JyeI"
    domains = ["180.189.154.30","intalock.com.au"]
    #domains = ["180.189.154.30"]
    #results = wxa.get_whois_info(api_key, domains)
    for d in domains:
        print(d)
        result = submit_query_single(api_key, d)
        print(result)
    #print(results)

test()

