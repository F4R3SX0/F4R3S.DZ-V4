#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F4R3S.DZ – Nmap Scanner (Simple Version)"""

import socket
import concurrent.futures

class NmapScanner:
    def __init__(self, target):
        self.target = target
        self.ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 5432, 5900, 6379, 8080, 8443]

    def scan(self):
        open_ports = []
        def check(port):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                if s.connect_ex((self.target, port)) == 0:
                    return {'port': port, 'state': 'open'}
                s.close()
            except:
                pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            for result in ex.map(check, self.ports):
                if result:
                    open_ports.append(result)

        return {'open_ports': open_ports, 'total': len(open_ports)}