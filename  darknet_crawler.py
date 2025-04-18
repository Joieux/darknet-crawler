#!/usr/bin/env python3
# darknet_crawler.py
# Enhanced crawler for .onion (darknet) sites using Tor

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import threading
import sqlite3
from queue import Queue

# Configuration
TOR_SOCKS_PROXY = 'socks5h://127.0.0.1:9050'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; DarknetCrawler/0.2; +https://example.com/bot)'
}
USE_SELENIUM = False
SELENIUM_DRIVER_PATH = '/path/to/geckodriver'

class DarknetCrawler:
    def __init__(self, db_path='crawler.db', delay=5):
        # Initialize persistent storage
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
        self.delay = delay
        self.lock = threading.Lock()
        self.queue = Queue()

        # HTTP session via Tor
        self.session = requests.Session()
        self.session.proxies = {
            'http': TOR_SOCKS_PROXY,
            'https': TOR_SOCKS_PROXY
        }
        self.session.headers.update(HEADERS)

        # Optional Selenium for dynamic content
        self.driver = None
        if USE_SELENIUM:
            from selenium import webdriver
            from selenium.webdriver.firefox.options import Options
            from selenium.webdriver.firefox.service import Service
            
            opts = Options()
            opts.headless = True
            
            # Creating a Firefox profile for Tor proxy settings
            profile = webdriver.FirefoxProfile()
            profile.set_preference('network.proxy.type', 1)
            profile.set_preference('network.proxy.socks', '127.0.0.1')
            profile.set_preference('network.proxy.socks_port', 9050)
            profile.set_preference('network.proxy.socks_remote_dns', True)
            
            # Updated to use Service class for the driver executable path
            service = Service(executable_path=SELENIUM_DRIVER_PATH)
            
            self.driver = webdriver.Firefox(
                service=service,
                firefox_profile=profile,
                options=opts
            )

    def _init_db(self):
        c = self.conn.cursor()
        c.execute(
            'CREATE TABLE IF NOT EXISTS urls (url TEXT PRIMARY KEY, visited INTEGER)'
        )
        self.conn.commit()

    def add_seed(self, url):
        """Add a starting URL to the crawl."""
        with self.lock:
            c = self.conn.cursor()
            c.execute(
                'INSERT OR IGNORE INTO urls (url, visited) VALUES (?, 0)',
                (url,)
            )
            self.conn.commit()
        self.queue.put(url)

    def authenticate(self, login_url, data):
        """Perform login to access invite-only sites."""
        resp = self.session.post(login_url, data=data)
        resp.raise_for_status()
        print('[+] Authenticated successfully')

    def fetch(self, url):
        """Fetch page content, respecting delay and optional dynamic rendering."""
        time.sleep(self.delay)
        try:
            if self.driver:
                self.driver.get(url)
                return self.driver.page_source
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"[-] Error fetching {url}: {e}")
            return ''

    def parse_links(self, html, base_url):
        """Extract .onion and HTTP(S) links from page."""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            href = urljoin(base_url, a['href'])
            parsed = urlparse(href)
            if parsed.scheme in ('http', 'https') and (parsed.netloc.endswith('.onion') or not parsed.netloc.endswith('.onion')):
                links.add(href)
        return links

    def mark_visited(self, url):
        with self.lock:
            c = self.conn.cursor()
            c.execute('UPDATE urls SET visited=1 WHERE url=?', (url,))
            self.conn.commit()

    def enqueue_new(self, links):
        """Persist and queue unseen links."""
        with self.lock:
            c = self.conn.cursor()
            for link in links:
                c.execute(
                    'INSERT OR IGNORE INTO urls (url, visited) VALUES (?, 0)',
                    (link,)
                )
                if c.rowcount > 0:  # Check if the row was actually inserted
                    self.queue.put(link)
            self.conn.commit()

    def crawl(self, threads=4):
        """Start crawling with worker threads."""
        def worker():
            while True:
                url = self.queue.get()
                try:
                    c = self.conn.cursor()
                    c.execute('SELECT visited FROM urls WHERE url=?', (url,))
                    result = c.fetchone()
                    if result is not None and result[0]:
                        self.queue.task_done()
                        continue
                        
                    html = self.fetch(url)
                    if html:  # Only process if we got content
                        links = self.parse_links(html, url)
                        self.mark_visited(url)
                        self.enqueue_new(links)
                        print(f'[+] Crawled {url} ({len(links)} new links)')
                    else:
                        print(f'[-] Failed to crawl {url}')
                except Exception as e:
                    print(f'[-] Error processing {url}: {e}')
                finally:
                    self.queue.task_done()

        for _ in range(threads):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
        
        try:
            self.queue.join()
        except KeyboardInterrupt:
            print('\n[!] Crawling interrupted by user')
        finally:
            if self.driver:
                self.driver.quit()
            self.conn.close()
            print('[+] Crawler shut down gracefully')

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Darknet Website-Centric Crawler')
    parser.add_argument('--seed', required=True, help='Starting .onion or HTTP(S) URL')
    parser.add_argument('--delay', type=int, default=5, help='Seconds between requests')
    parser.add_argument('--db', default='crawler.db', help='SQLite database path')
    parser.add_argument('--threads', type=int, default=4, help='Number of worker threads')
    parser.add_argument('--login-url', help='URL for authentication')
    parser.add_argument('--login-data', nargs='*', help='Key=value pairs for login form')

    args = parser.parse_args()

    crawler = DarknetCrawler(db_path=args.db, delay=args.delay)
    crawler.add_seed(args.seed)
    if args.login_url and args.login_data:
        data = dict(item.split('=') for item in args.login_data)
        crawler.authenticate(args.login_url, data)
    
    try:
        crawler.crawl(threads=args.threads)
    except Exception as e:
        print(f'[!] Fatal error: {e}')