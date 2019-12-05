#!/usr/bin/env python

import sys

from splunklib.searchcommands import Configuration
from splunklib.searchcommands import dispatch
from splunklib.searchcommands import StreamingCommand
from splunklib.searchcommands import Option
from splunklib.searchcommands import validators

import urllib, urllib2
import json
#import itertools

import wxa

@Configuration()
class whoisxmlapiCommand(StreamingCommand):

    def stream(self, records):
        self.logger.debug('CountMatchesCommand: %s', self)  # logs command line

        storage_passwords=self.service.storage_passwords

        # need to handle a missing key gracefully
        try:
            retrievedCredential = [k for k in storage_passwords if k.content.get('username')=='whoisxmlapi_api_key'][0]

        except Exception, e:
            error = "error retrieving API key - is it defined?: %s " % ( e )
            for record in records:
                record["error"] = error
                yield record
            return

        api_key = retrievedCredential.content.get('clear_password')

        # build a unique list of domains

        domains = {}
        
        record_list = list(records)
        for r in record_list:
            domains[r['domain']] = 1

        results = wxa.get_whois_info(api_key, domains.keys())

        # do query using the wxa module (which will handle paging, waiting, looping)
        # iterate through each record, adding the required fields

        # FAKE DATA
        #results = {'google.com':'Alphabet', 'yahoo.com': 'Someone'}

        for r in record_list:
            domain = r['domain']
            if domain in results:
                #r["owner"] = str(results[domain])
                for k in results[domain]:
                    r[k] = results[domain][k]
            else:
                r['owner'] = "Unknown"
            yield r

dispatch(whoisxmlapiCommand, sys.argv, sys.stdin, sys.stdout, __name__)
