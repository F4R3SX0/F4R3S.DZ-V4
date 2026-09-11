#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F4R3S.DZ – Report Generator"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

class ReportGenerator:
    def __init__(self, results, target):
        self.results = results
        self.target = target
        os.makedirs('reports', exist_ok=True)

    def generate(self):
        filename = f"reports/F4R3S_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, 800, "F4R3S.DZ Security Report")
        c.setFont("Helvetica", 12)
        c.drawString(50, 770, f"Target: {self.target}")
        c.drawString(50, 750, f"Vulnerabilities: {len(self.results.get('vulnerabilities', []))}")
        c.save()
        return filename