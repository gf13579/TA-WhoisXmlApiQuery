import os
import sys
import time
import datetime
import requests
#from urllib.request import urlopen
from urllib2 import urlopen
import json
import logging
import time

def get_whois_info(api_key, domains, max_records=100, wait_time=10, max_iterations=6):
    request_id = submit_query(api_key, domains)
    time.sleep(wait_time)
    results = retrieve_results(api_key, request_id, max_records, wait_time, max_iterations)
    return results


def submit_query(api_key, domains):
    base_url = 'https://www.whoisxmlapi.com'
    headers = {
        "Content-Type" : "application/json"
    }

    payload = {
        "apiKey": api_key,
        "domains": domains, 
        "outputFormat": "JSON"
    }

    response = requests.post(base_url + '/BulkWhoisLookup/bulkServices/bulkWhois',data=json.dumps(payload),headers=headers,verify=False)
    if response.status_code != 200:
        logging.warning("Failed to connect or authenticate")
        logging.info(response.content)
        exit()

    return json.loads(response.content)['requestId']

def retrieve_results(api_key, request_id, max_records, wait_time, max_iterations):
    base_url = 'https://www.whoisxmlapi.com'
    headers = {
        "Content-Type" : "application/json"
    }
    payload = {
        "apiKey": api_key,
        "requestId": request_id,
        "maxRecords": max_records,
        "startIndex": 1,
        "outputFormat": "JSON"
    }
    response = requests.post(base_url + '/BulkWhoisLookup/bulkServices/getRecords',data=json.dumps(payload),headers=headers,verify=False)
    if response.status_code != 200:
        logging.warning("Failed to connect or authenticate")
        logging.info(response.content)
        exit()

    #print response.content

    if json.loads(response.content)['recordsLeft'] > 0:
        for i in range(1,max_iterations):
            time.sleep(wait_time)
            response = requests.post(base_url + '/BulkWhoisLookup/bulkServices/getRecords',data=json.dumps(payload),headers=headers,verify=False)
            if json.loads(response.content)['recordsLeft'] == 0:
                break

    #print response.content
    retDict = {}
    for r in json.loads(response.content)['whoisRecords']:
        # assemble a cut-down object
        new_rec = {}
        new_rec['contactEmail'] = r['whoisRecord']['contactEmail']
        new_rec['registrarName'] = r['whoisRecord']['registrarName']
        new_rec['organization'] = r['whoisRecord']['registryData']['registrant']['organization']
        new_rec['street1'] = r['whoisRecord']['registryData']['registrant']['street1']
        new_rec['postalCode'] = r['whoisRecord']['registryData']['registrant']['postalCode']
        retDict[r['domainName']] = new_rec

    return retDict

def submit_queries(api_key,domains):
    retDict = {}
    for d in domains:
        new_rec = submit_query_single(api_key,d)
        retDict[d] = new_rec
    
    return retDict

def submit_query_single(api_key, domain):
    url = 'https://www.whoisxmlapi.com/whoisserver/WhoisService?' + 'domainName=' + domain + '&apiKey=' + api_key + "&outputFormat=JSON"

    response = requests.get(url)
    rec = json.loads(response.content)

    new_rec = {}
    try:
        new_rec['domainName'] = domain
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


#test()
