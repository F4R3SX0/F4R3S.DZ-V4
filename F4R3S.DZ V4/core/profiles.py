#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F4R3S.DZ – Profiles"""

PROFILES = {
    'deep': {
        'name': 'Deep',
        'tools': 74,
        'depth': 'maximum',
        'description': 'Full scan with all modules'
    },
    'quick': {
        'name': 'Quick',
        'tools': 8,
        'depth': 'quick',
        'description': 'Fast scan'
    }
}


def get_profile(key):
    return PROFILES.get(key, PROFILES['deep'])