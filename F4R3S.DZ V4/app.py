#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F4R3S.DZ – Web Dashboard v4.0
"""

import os
import sys
import json
import time
import secrets
import threading
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO

from core.profiles import PROFILES, get_profile
from core.pipeline import PipelineEngine
from core.license_manager import LicenseManager

# ============================================================
# Configuration
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYS_FILE = os.environ.get('KEYS_FILE', os.path.join(BASE_DIR, 'keys.json'))

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize
license_mgr = LicenseManager(keys_file=KEYS_FILE)

# ============================================================
# LOGIN TEMPLATE (English)
# ============================================================
LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>F4R3S.DZ - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0e14;
            background-image: url('data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800" opacity="0.06"%3E%3Ctext x="100" y="200" font-size="100" fill="%232d8cff" font-family="monospace" font-weight="bold"%3ESYSTEM OVERRIDE%3C/text%3E%3Ctext x="300" y="400" font-size="120" fill="%232d8cff" font-family="monospace" font-weight="bold"%3ES!L3NT%3C/text%3E%3Ctext x="500" y="600" font-size="110" fill="%232d8cff" font-family="monospace" font-weight="bold"%3EK!LL3R%3C/text%3E%3C/svg%3E');
            background-size: cover;
            background-position: center;
            color: #c8d0dc;
            font-family: 'Segoe UI', sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-box {
            background: rgba(26, 31, 43, 0.95);
            padding: 45px;
            border-radius: 18px;
            border: 1px solid #2a3342;
            width: 440px;
            text-align: center;
            box-shadow: 0 25px 70px rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            animation: fadeIn 0.6s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .icon { font-size: 52px; }
        h1 {
            color: #2d8cff;
            font-weight: 300;
            font-size: 30px;
            margin: 12px 0;
        }
        h1 span { font-weight: 700; }
        .subtitle {
            color: #8a9bb5;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group { margin-bottom: 18px; text-align: left; }
        .form-group label {
            display: block;
            color: #8a9bb5;
            font-size: 13px;
            margin-bottom: 6px;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 14px 18px;
            background: #0e1219;
            border: 1px solid #2a3342;
            border-radius: 10px;
            color: #c8d0dc;
            font-size: 16px;
            outline: none;
            transition: 0.3s;
            font-family: 'Courier New', monospace;
        }
        input:focus {
            border-color: #2d8cff;
            box-shadow: 0 0 15px rgba(45, 140, 255, 0.3);
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #2d8cff, #0066cc);
            border: none;
            border-radius: 10px;
            color: #fff;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            margin-top: 10px;
            transition: 0.3s;
            letter-spacing: 1px;
        }
        button:hover {
            background: linear-gradient(135deg, #1a6fd4, #0055aa);
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(45, 140, 255, 0.4);
        }
        .error {
            color: #ff4444;
            margin-top: 18px;
            padding: 12px;
            background: rgba(255, 68, 68, 0.1);
            border-radius: 8px;
            font-size: 14px;
            border: 1px solid rgba(255, 68, 68, 0.3);
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #1e2633;
            color: #5a6f8c;
            font-size: 12px;
        }
        .telegram-btn {
            display: inline-block;
            background: #0088cc;
            color: #fff;
            padding: 10px 24px;
            border-radius: 30px;
            text-decoration: none;
            font-weight: bold;
            font-size: 14px;
            margin: 12px 0;
            transition: 0.3s;
        }
        .telegram-btn:hover {
            background: #006699;
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(0, 136, 204, 0.4);
        }
        .dev-links {
            margin-top: 15px;
            display: flex;
            justify-content: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .dev-links a {
            color: #2d8cff;
            text-decoration: none;
            padding: 4px 12px;
            border: 1px solid #2a3342;
            border-radius: 20px;
            font-size: 12px;
            transition: 0.3s;
        }
        .dev-links a:hover {
            background: #2d8cff;
            color: #0a0e14;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <div class="icon">🐉</div>
        <h1><span>F4R3S</span>.DZ</h1>
        <p class="subtitle">Enter your credentials to access the scanner</p>
        <form method="post">
            <div class="form-group">
                <label>👤 Username</label>
                <input type="text" name="username" placeholder="Enter your username" required autocomplete="username" autofocus>
            </div>
            <div class="form-group">
                <label>🔑 License Key</label>
                <input type="text" name="license_key" placeholder="F4R3S-XXXX-XXXX" required autocomplete="off">
            </div>
            <button type="submit">🚀 UNLOCK SCANNER</button>
        </form>
        {% if error %}
            <div class="error">❌ {{ error }}</div>
        {% endif %}
        <div class="footer">
            <p style="margin-bottom: 8px;">💬 To get a license key, contact the developer:</p>
            <a href="https://t.me/H4Ck3R0D4Y" target="_blank" class="telegram-btn">📱 @H4Ck3R0D4Y</a>
            <div class="dev-links">
                <a href="https://x.com/faresdahoumane" target="_blank">🐦 X</a>
                <a href="https://www.linkedin.com/in/fares-dahoumane-364518412" target="_blank">🔗 LinkedIn</a>
                <a href="https://github.com/F4R3SX0" target="_blank">🐙 GitHub</a>
            </div>
        </div>
    </div>
</body>
</html>
'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        key = request.form.get('license_key', '').strip().upper()

        if not username or not key:
            error = "Please enter both username and license key"
        else:
            valid, msg, days_left, customer = license_mgr.verify(key)

            if valid and customer.lower() == username.lower():
                session['license_key'] = key
                session['username'] = customer
                session['client_ip'] = request.remote_addr
                session['days_left'] = days_left
                return redirect(url_for('dashboard'))

            elif valid:
                error = "Username does not match this license key"
            else:
                error = msg

    return render_template_string(LOGIN_HTML, error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = session.get('license_key')
        if not key:
            return redirect(url_for('login'))
        valid, msg, _, _ = license_mgr.verify(key)
        if not valid:
            session.clear()
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ============================================================
# DASHBOARD (English)
# ============================================================
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F4R3S.DZ Scanner</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0e14;
            color: #c8d0dc;
            font-family: 'Segoe UI', sans-serif;
            padding: 20px;
            min-height: 100vh;
            background-image: url('data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800" opacity="0.05"%3E%3Ctext x="100" y="200" font-size="100" fill="%232d8cff" font-family="monospace" font-weight="bold"%3ESYSTEM OVERRIDE%3C/text%3E%3Ctext x="300" y="400" font-size="120" fill="%232d8cff" font-family="monospace" font-weight="bold"%3ES!L3NT%3C/text%3E%3Ctext x="500" y="600" font-size="110" fill="%232d8cff" font-family="monospace" font-weight="bold"%3EK!LL3R%3C/text%3E%3C/svg%3E');
            background-size: cover;
            background-attachment: fixed;
        }
        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(10, 14, 20, 0.9);
            padding: 12px 20px;
            border-radius: 12px;
            border: 1px solid #2a3342;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
            backdrop-filter: blur(10px);
        }
        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }
        .username {
            color: #2d8cff;
            font-weight: 700;
        }
        .days-badge {
            background: #4caf50;
            color: #fff;
            padding: 3px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }
        .days-badge.warning { background: #ff8800; }
        .days-badge.danger { background: #ff4444; }
        .ip-badge {
            color: #64b5f6;
            font-size: 12px;
        }
        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }
        .social-links a {
            color: #8a9bb5;
            text-decoration: none;
            margin: 0 4px;
            padding: 5px 12px;
            border: 1px solid #2a3342;
            border-radius: 20px;
            font-size: 12px;
            transition: 0.3s;
            display: inline-block;
        }
        .social-links a:hover {
            color: #2d8cff;
            border-color: #2d8cff;
            background: rgba(45, 140, 255, 0.1);
        }
        .logout-btn {
            background: #ff4444;
            color: #fff;
            padding: 6px 18px;
            border-radius: 20px;
            text-decoration: none;
            font-weight: 600;
            font-size: 13px;
            transition: 0.3s;
        }
        .logout-btn:hover { background: #cc0000; }
        .main-header {
            display: flex;
            align-items: center;
            gap: 20px;
            border-bottom: 2px solid #2d8cff;
            padding: 15px 20px;
            margin-bottom: 25px;
            background: rgba(10, 14, 20, 0.85);
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }
        .main-header .icon { font-size: 48px; }
        .main-header h1 {
            font-size: 28px;
            color: #2d8cff;
            font-weight: 300;
        }
        .main-header h1 span { font-weight: 700; }
        .status {
            margin-left: auto;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            color: #8a9bb5;
        }
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .status-dot.green { background: #4caf50; box-shadow: 0 0 10px #4caf50; }
        .status-dot.yellow {
            background: #ffbb33;
            box-shadow: 0 0 10px #ffbb33;
            animation: pulse 1s infinite;
        }
        .status-dot.red { background: #ff4444; box-shadow: 0 0 10px #ff4444; }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.8); }
        }
        .scan-box {
            background: rgba(26, 31, 43, 0.9);
            padding: 25px 30px;
            border-radius: 12px;
            border: 1px solid #2a3342;
            margin-bottom: 25px;
            backdrop-filter: blur(5px);
        }
        .scan-input-group {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
        }
        .scan-input-group input {
            flex: 1;
            min-width: 200px;
            padding: 13px 18px;
            background: #0e1219;
            border: 1px solid #2a3342;
            border-radius: 10px;
            color: #c8d0dc;
            font-size: 15px;
            outline: none;
            transition: 0.3s;
        }
        .scan-input-group input:focus {
            border-color: #2d8cff;
            box-shadow: 0 0 15px rgba(45, 140, 255, 0.2);
        }
        .scan-input-group select {
            padding: 13px 18px;
            background: #0e1219;
            border: 1px solid #2a3342;
            border-radius: 10px;
            color: #c8d0dc;
            font-size: 15px;
            cursor: pointer;
        }
        .scan-input-group button {
            padding: 13px 32px;
            background: linear-gradient(135deg, #2d8cff, #0066cc);
            border: none;
            border-radius: 10px;
            color: #fff;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            transition: 0.3s;
        }
        .scan-input-group button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(45, 140, 255, 0.4);
        }
        .scan-input-group button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .export-btn { background: linear-gradient(135deg, #4caf50, #2e7d32) !important; }
        .log-container {
            background: rgba(14, 18, 25, 0.95);
            padding: 15px;
            border-radius: 10px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            border: 1px solid #2a3342;
            margin-top: 15px;
        }
        .log-container::-webkit-scrollbar { width: 8px; }
        .log-container::-webkit-scrollbar-track { background: #0e1219; }
        .log-container::-webkit-scrollbar-thumb { background: #2d8cff; border-radius: 10px; }
        .log-entry {
            padding: 4px 0;
            border-bottom: 1px solid #1a1f2b;
            word-break: break-all;
        }
        .log-entry.success { color: #4caf50; }
        .log-entry.error { color: #ff4444; }
        .log-entry.info { color: #64b5f6; }
        .log-entry.warning { color: #ffbb33; }
        .loading-overlay {
            display: none;
            text-align: center;
            padding: 30px;
            background: rgba(26, 31, 43, 0.9);
            border-radius: 12px;
            border: 2px solid #2d8cff;
            margin-top: 20px;
            backdrop-filter: blur(5px);
        }
        .loading-overlay .spinner {
            width: 60px;
            height: 60px;
            border: 6px solid #2a3342;
            border-top: 6px solid #2d8cff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .results-area { display: none; margin-top: 25px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: rgba(26, 31, 43, 0.9);
            padding: 18px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #2a3342;
            transition: 0.3s;
        }
        .stat-card:hover { transform: translateY(-3px); }
        .stat-card .num { font-size: 30px; font-weight: 700; }
        .stat-card .num.critical { color: #ff4444; }
        .stat-card .num.high { color: #ff8800; }
        .stat-card .num.medium { color: #ffbb33; }
        .stat-card .num.low { color: #4caf50; }
        .stat-card .label {
            color: #8a9bb5;
            font-size: 12px;
            text-transform: uppercase;
            margin-top: 6px;
            letter-spacing: 1px;
        }
        .findings-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            background: rgba(26, 31, 43, 0.9);
            border-radius: 10px;
            overflow: hidden;
        }
        .findings-table th {
            text-align: left;
            padding: 12px 15px;
            border-bottom: 2px solid #2a3342;
            color: #8a9bb5;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .findings-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #1e2633;
            color: #c8d0dc;
        }
        .findings-table tr:hover { background: #232a38; }
        .severity-badge {
            padding: 4px 14px;
            border-radius: 30px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .sev-critical { background: #ff4444; color: #fff; }
        .sev-high { background: #ff8800; color: #fff; }
        .sev-medium { background: #ffbb33; color: #000; }
        .sev-low { background: #4caf50; color: #fff; }
        .footer {
            text-align: center;
            padding: 20px;
            border-top: 1px solid #1e2633;
            margin-top: 30px;
            color: #5a6f8c;
            font-size: 13px;
            background: rgba(10, 14, 20, 0.8);
            border-radius: 12px;
        }
        .footer a {
            color: #8a9bb5;
            text-decoration: none;
            margin: 0 10px;
            transition: 0.3s;
        }
        .footer a:hover { color: #2d8cff; }
        @media (max-width: 768px) {
            .scan-input-group { flex-direction: column; }
            .scan-input-group input,
            .scan-input-group select,
            .scan-input-group button { width: 100%; }
            .top-bar { flex-direction: column; }
        }
    </style>
</head>
<body>

    <div class="top-bar">
        <div class="user-info">
            <span class="username">👤 {{ username }}</span>
            <span class="days-badge {% if days_left < 7 %}danger{% elif days_left < 30 %}warning{% endif %}">
                📅 {{ days_left }} days left
            </span>
            <span class="ip-badge">🌍 IP: {{ client_ip }}</span>
        </div>
        <div class="header-actions">
            <div class="social-links">
                <a href="https://x.com/faresdahoumane" target="_blank">🐦 X</a>
                <a href="https://www.linkedin.com/in/fares-dahoumane-364518412" target="_blank">🔗 LinkedIn</a>
                <a href="https://github.com/F4R3SX0" target="_blank">🐙 GitHub</a>
                <a href="https://t.me/H4Ck3R0D4Y" target="_blank">💬 Telegram</a>
            </div>
            <a href="/logout" class="logout-btn">🚪 Logout</a>
        </div>
    </div>

    <div class="main-header">
        <span class="icon">🐉</span>
        <h1><span>F4R3S</span>.DZ Ultimate Scanner</h1>
        <div class="status">
            <span class="status-dot green" id="statusDot"></span>
            <span id="statusText">Ready</span>
        </div>
    </div>

    <div class="scan-box">
        <h3 style="margin-bottom: 15px; color: #2d8cff;">🎯 Target Configuration</h3>
        <div class="scan-input-group">
            <input type="text" id="target" placeholder="https://example.com" value="https://example.com/">
            <select id="profile">
                <option value="deep">Deep Scan (Full)</option>
                <option value="quick">Quick Scan</option>
            </select>
            <button onclick="launchScan()" id="scanBtn">🚀 Scan</button>
            <button class="export-btn" onclick="exportResults()" id="exportBtn" style="display:none;">💾 Export</button>
        </div>
    </div>

    <div class="loading-overlay" id="loadingOverlay">
        <div class="spinner"></div>
        <div style="color: #fff; font-size: 18px;">🔍 Scanning in progress...</div>
    </div>

    <div class="log-container" id="logContainer">
        <div class="log-entry info">[+] Scanner ready</div>
        <div class="log-entry info">[+] Awaiting target...</div>
    </div>

    <div class="results-area" id="resultsArea">
        <h3 style="margin: 20px 0 15px; color: #2d8cff;">📊 Scan Results</h3>
        <div class="stats-grid">
            <div class="stat-card"><div class="num critical" id="critCount">0</div><div class="label">Critical</div></div>
            <div class="stat-card"><div class="num high" id="highCount">0</div><div class="label">High</div></div>
            <div class="stat-card"><div class="num medium" id="medCount">0</div><div class="label">Medium</div></div>
            <div class="stat-card"><div class="num low" id="lowCount">0</div><div class="label">Low</div></div>
        </div>
        <table class="findings-table">
            <thead>
                <tr>
                    <th>Severity</th>
                    <th>Type</th>
                    <th>URL / Details</th>
                </tr>
            </thead>
            <tbody id="findingsBody"></tbody>
        </table>
    </div>

    <footer class="footer">
        <div>🐉 Developed by <strong style="color: #2d8cff;">F4R3S.DZ</strong></div>
        <div style="margin-top: 10px;">
            <a href="https://x.com/faresdahoumane" target="_blank">🐦 X</a>
            <a href="https://www.linkedin.com/in/fares-dahoumane-364518412" target="_blank">🔗 LinkedIn</a>
            <a href="https://github.com/F4R3SX0" target="_blank">🐙 GitHub</a>
            <a href="https://t.me/H4Ck3R0D4Y" target="_blank">💬 @H4Ck3R0D4Y</a>
        </div>
    </footer>

    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <script>
        const socket = io();
        let resultsData = null;

        socket.on('connect', () => addLog('[+] Connected to server', 'success'));
        socket.on('scan_log', (d) => addLog(d.message, d.type));
        socket.on('pipeline_progress', (d) => addLog(`[*] ${d.progress}% - ${d.step}`, 'info'));

        socket.on('pipeline_complete', (d) => {
            resultsData = d.results;
            displayResults(d.results);
            document.getElementById('loadingOverlay').style.display = 'none';
            document.getElementById('scanBtn').disabled = false;
            document.getElementById('exportBtn').style.display = 'inline-block';
            addLog('[+] Scan completed successfully!', 'success');
        });

        socket.on('pipeline_error', (d) => {
            addLog('[!] Error: ' + d.error, 'error');
            document.getElementById('loadingOverlay').style.display = 'none';
            document.getElementById('scanBtn').disabled = false;
        });

        function addLog(msg, type) {
            type = type || 'info';
            const c = document.getElementById('logContainer');
            const e = document.createElement('div');
            e.className = 'log-entry ' + type;
            e.textContent = msg;
            c.appendChild(e);
            c.scrollTop = c.scrollHeight;
        }

        function launchScan() {
            const t = document.getElementById('target').value.trim();
            const p = document.getElementById('profile').value;
            if (!t) { alert('Please enter a target URL'); return; }

            document.getElementById('scanBtn').disabled = true;
            document.getElementById('exportBtn').style.display = 'none';
            document.getElementById('resultsArea').style.display = 'none';
            document.getElementById('logContainer').innerHTML = '';
            document.getElementById('loadingOverlay').style.display = 'block';

            addLog('[+] Target: ' + t, 'info');
            addLog('[+] Profile: ' + p, 'info');

            fetch('/api/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({target: t, profile: p})
            })
            .then(r => r.json())
            .then(d => {
                if (d.status === 'started') {
                    addLog('[+] Scan started: ' + d.task_id, 'success');
                } else {
                    addLog('[!] Error: ' + d.error, 'error');
                    document.getElementById('loadingOverlay').style.display = 'none';
                    document.getElementById('scanBtn').disabled = false;
                }
            })
            .catch(e => {
                addLog('[!] Error: ' + e, 'error');
                document.getElementById('loadingOverlay').style.display = 'none';
                document.getElementById('scanBtn').disabled = false;
            });
        }

        function displayResults(r) {
            document.getElementById('resultsArea').style.display = 'block';
            const v = r.vulnerabilities || [];
            document.getElementById('critCount').textContent = v.filter(x => x.severity === 'CRITICAL').length;
            document.getElementById('highCount').textContent = v.filter(x => x.severity === 'HIGH').length;
            document.getElementById('medCount').textContent = v.filter(x => x.severity === 'MEDIUM').length;
            document.getElementById('lowCount').textContent = v.filter(x => x.severity === 'LOW').length;

            const tb = document.getElementById('findingsBody');
            tb.innerHTML = '';

            if (v.length === 0) {
                tb.innerHTML = '<tr><td colspan="3" style="text-align:center;color:#4caf50;padding:20px;">No vulnerabilities found</td></tr>';
                return;
            }

            v.forEach(x => {
                const tr = document.createElement('tr');
                const cls = 'sev-' + x.severity.toLowerCase();
                tr.innerHTML = `<td><span class="severity-badge ${cls}">${x.severity}</span></td>
                                <td>${x.type || 'Unknown'}</td>
                                <td style="font-size:13px;word-break:break-all;">
                                    ${x.url || x.description || 'N/A'}
                                    ${x.parameter ? '<br>🔑 Param: ' + x.parameter : ''}
                                    ${x.payload ? '<br>💉 Payload: ' + x.payload : ''}
                                </td>`;
                tb.appendChild(tr);
            });
        }

        function exportResults() {
            if (!resultsData) { alert('No results to export'); return; }
            const blob = new Blob([JSON.stringify(resultsData, null, 2)], {type: 'application/json'});
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'scan_results.json';
            a.click();
        }
    </script>
</body>
</html>
'''


@app.route('/')
@require_login
def dashboard():
    return render_template_string(
        DASHBOARD_HTML,
        username=session.get('username', 'Guest'),
        days_left=session.get('days_left', 0),
        client_ip=session.get('client_ip', 'Unknown')
    )


# ============================================================
# API
# ============================================================
@app.route('/api/scan', methods=['POST'])
@require_login
def start_scan():
    data = request.json
    target = data.get('target')
    profile_key = data.get('profile', 'deep')

    if not target:
        return jsonify({'error': 'Target is required'}), 400

    username = session.get('username', 'Guest')
    profile = get_profile(profile_key)
    task_id = f"scan_{int(time.time())}"

    def run():
        try:
            engine = PipelineEngine(target, profile, socketio)
            results = engine.run()

            if 'start_time' in results:
                results['start_time'] = str(results['start_time'])
            if 'end_time' in results:
                results['end_time'] = str(results['end_time'])

            socketio.emit('pipeline_complete', {'results': results})
        except Exception as e:
            socketio.emit('pipeline_error', {'error': str(e)})

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'status': 'started', 'task_id': task_id})


# ============================================================
# WSGI entry point for Railway
# ============================================================
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8090))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
