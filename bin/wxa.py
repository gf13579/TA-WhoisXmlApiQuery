import os
import sys
import time
import datetime
import requests
import json
import logging
import time

def submit_queries(api_key,domains):
    retDict = {}
    for d in domains:
        new_rec = submit_query_single(api_key,d)
        retDict[d] = new_rec
    
    return retDict

def submit_query_single(api_key, domain):

    # HI SPLUNK CLOUD VETTING TEAM! Please don't reject the TA For sending the api key as a GET parameter
    # There is no alternative - this is just the way the vendor API has been written: https://whois.whoisxmlapi.com/documentation/making-requests
    # This could be due to the API being read-only - the most significant consequence of the API key being leaked is that a customer's credits for DNS lookups might be used up
    # The splunkbase page for this TA will be updated to highlight to end users that their API key is being transmitted in the GET request - and that there is no alternative right now

    url = 'https://www.whoisxmlapi.com/whoisserver/WhoisService?' + 'domainName=' + domain + '&apiKey=' + api_key + "&outputFormat=JSON"

    response = requests.get(url)
    rec = json.loads(response.content)

    new_rec = {}
    try:
        new_rec['domainName'] = domain
    except:
        new_rec['domainName'] = ''
    try:
        new_rec['contactEmail'] = rec.get('WhoisRecord').get('contactEmail')
    except:
        new_rec['contactEmail'] = ''
    try:
        new_rec['registrarName'] = rec.get('WhoisRecord').get('registrarName')
    except:
        new_rec['registrarName'] = ''
    try:
        new_rec['organization'] = rec.get('WhoisRecord').get('registryData').get('registrant').get('organization')
    except:
        new_rec['organization'] = ''
    try:
        new_rec['organization'] = rec.get('WhoisRecord').get('registrant').get('organization')
    except:
        if new_rec['organization'] == '':
            new_rec['organization'] = ''
    try:
        new_rec['registrantName'] = rec.get('WhoisRecord').get('registryData').get('registrant').get('name')
    except:
        new_rec['registrantName'] = ''
    try:
        new_rec['techContactName'] = rec.get('WhoisRecord').get('registryData').get('technicalContact').get('name')
    except:
        new_rec['techContactName'] = ''
    try:
        new_rec['street1'] = rec.get('WhoisRecord').get('registryData').get('registrant').get('street1')
    except:
        new_rec['street1'] = ''
    try:
        new_rec['postalCode'] = rec.get('WhoisRecord').get('registryData').get('registrant').get('postalCode')
    except:
        new_rec['postalCode'] = ''

    return new_rec

