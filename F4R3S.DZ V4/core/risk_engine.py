#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F4R3S.DZ – Risk Engine"""

class RiskEngine:
    def assess(self, vuln):
        severity = vuln.get('severity', 'INFO')
        scores = {'CRITICAL': 9.5, 'HIGH': 7.5, 'MEDIUM': 5.0, 'LOW': 2.0, 'INFO': 0.5}
        return {'score': scores.get(severity, 0), 'severity': severity}