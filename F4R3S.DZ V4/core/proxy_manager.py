#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F4R3S.DZ – Proxy Manager"""

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.index = 0

    def add(self, proxy):
        self.proxies.append(proxy)

    def get_next(self):
        if not self.proxies:
            return None
        p = self.proxies[self.index]
        self.index = (self.index + 1) % len(self.proxies)
        return {'http': p, 'https': p}