#!/usr/bin/env python

import sys

from splunklib.searchcommands import Configuration
from splunklib.searchcommands import dispatch
from splunklib.searchcommands import StreamingCommand
from splunklib.searchcommands import Option
from splunklib.searchcommands import validators

# import urllib, urllib2
import json

import wxa

@Configuration()
class whoisxmlapiCommand(StreamingCommand):

    def stream(self, records):
        self.logger.debug('whoisxmlapiCommand: %s', self)  # logs command line

        storage_passwords=self.service.storage_passwords

        # need to handle a missing key gracefully
        try:
            retrievedCredential = [k for k in storage_passwords if k.content.get('username')=='whoisxmlapi_api_key'][0]

        except Exception as e:
            error = "error retrieving API key - is it defined?: %s " % ( e )
            for record in records:
                record["error"] = error
                yield record
            return

        api_key = retrievedCredential.content.get('clear_password')

        result_cache = {}

        #record_list = list(records)
        for r in records:
            if r['domain'] in result_cache:
                existing_record = result_cache[r['domain']]
                r.update(existing_record)
            else:
                self.logger.info('Querying: %s', r['domain'])
                result = wxa.submit_query_single(api_key, r['domain'])
                r.update(result)
                result_cache[r['domain']] = result
            yield r

        return

dispatch(whoisxmlapiCommand, sys.argv, sys.stdin, sys.stdout, __name__)
