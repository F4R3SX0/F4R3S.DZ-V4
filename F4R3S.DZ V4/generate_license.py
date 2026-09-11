#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F4R3S.DZ – License Generator (Developer Tool)
"""

import os
import sys
import json
import secrets
from datetime import datetime, timedelta

KEYS_FILE = os.environ.get('KEYS_FILE',
                          os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys.json'))


def load_keys():
    try:
        if os.path.exists(KEYS_FILE):
            with open(KEYS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}


def save_keys(keys):
    d = os.path.dirname(KEYS_FILE)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    with open(KEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(keys, f, indent=4, ensure_ascii=False)


def create_license(customer_name, days=365):
    """Create a new license key"""
    keys = load_keys()

    # Generate a secure key
    raw = secrets.token_hex(6).upper()
    key = f"F4R3S{raw}"

    # Ensure uniqueness
    while key in keys:
        raw = secrets.token_hex(6).upper()
        key = f"F4R3S{raw}"

    keys[key] = {
        'customer': customer_name,
        'created': datetime.now().isoformat(),
        'expiry': (datetime.now() + timedelta(days=days)).isoformat(),
        'active': True
    }
    save_keys(keys)
    return key


if __name__ == "__main__":
    print("=" * 60)
    print("🔑 F4R3S.DZ - License Generator")
    print("=" * 60)
    print(f"📁 Keys file: {KEYS_FILE}")
    print()

    name = input("👤 Customer name: ").strip()
    if not name:
        print("❌ Name is required")
        sys.exit(1)

    days_input = input("📅 Duration in days (365 = 1 year): ").strip()
    days = int(days_input) if days_input else 365

    key = create_license(name, days)

    print()
    print("=" * 60)
    print("✅ LICENSE CREATED SUCCESSFULLY")
    print("=" * 60)
    print(f"🔑 Key:      {key}")
    print(f"👤 Customer: {name}")
    print(f"📅 Expires:  {(datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')}")
    print(f"⏱️  Duration: {days} days")
    print("=" * 60)
    print()
    print("📧 Send this message to the customer:")
    print()
    print(f"   🎉 Welcome {name}!")
    print(f"   🔑 Your key: {key}")
    print(f"   📅 Valid until: {(datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')}")
    print(f"   ⚠️  Keep it secret!")