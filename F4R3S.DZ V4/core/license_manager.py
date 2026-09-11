#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F4R3S.DZ – License Manager
"""

import os
import json
from datetime import datetime


class LicenseManager:
    """Simple license manager using keys.json"""

    def __init__(self, keys_file='keys.json'):
        self.keys_file = keys_file

    def _load_keys(self):
        try:
            if os.path.exists(self.keys_file):
                with open(self.keys_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def verify(self, key):
        """
        Verify a license key.
        Returns: (is_valid, message, days_left, customer_name)
        """
        keys = self._load_keys()

        if key not in keys:
            return False, "Invalid license key", 0, "Unknown"

        data = keys[key]

        if not data.get('active', True):
            return False, "License key is deactivated", 0, data.get('customer', 'Unknown')

        try:
            expiry = datetime.fromisoformat(data['expiry'])
            if datetime.now() > expiry:
                days_overdue = (datetime.now() - expiry).days
                return False, f"License expired {days_overdue} days ago", 0, data.get('customer', 'Unknown')
            days_left = (expiry - datetime.now()).days
        except:
            return False, "Invalid expiry date", 0, data.get('customer', 'Unknown')

        return True, "Valid", days_left, data.get('customer', 'Unknown')

    def get_customer_name(self, key):
        keys = self._load_keys()
        return keys.get(key, {}).get('customer', 'Unknown')