#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F4R3S.DZ – CVE Lookup"""

import requests

class CVELookup:
    def __init__(self):
        self.cache = {}

    def lookup(self, service, version=''):
        key = f"{service}:{version}"
        if key in self.cache:
            return self.cache[key]
        try:
            url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={service}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                vulns = []
                for v in data.get('vulnerabilities', [])[:3]:
                    cve = v.get('cve', {})
                    vulns.append({'id': cve.get('id', 'N/A'), 'description': 'CVE found'})
                self.cache[key] = vulns
                return vulns
        except:
            pass
        return []