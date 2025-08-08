"""
Test script to verify scraper protection is working
"""

import requests
import time

# Test the rate limiting
url = 'http://127.0.0.1:5000/articles'

print("Testing anti-scraping protection...")
print("=" * 50)

# Test normal requests
print("\n1. Testing normal requests (should succeed):")
for i in range(5):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        print(f"Request {i+1}: Status {response.status_code}")
        time.sleep(1)  # Wait 1 second between requests
    except Exception as e:
        print(f"Request {i+1}: Error - {e}")

# Test rapid requests (should trigger rate limiting)
print("\n2. Testing rapid requests (should trigger rate limiting):")
for i in range(70):  # More than 60 per minute limit
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        if response.status_code == 429:
            print(f"Request {i+1}: Rate limited! (Status 429)")
            break
        else:
            print(f"Request {i+1}: Status {response.status_code}")
    except Exception as e:
        print(f"Request {i+1}: Error - {e}")

# Test suspicious user agent
print("\n3. Testing suspicious user agent:")
suspicious_agents = [
    'python-requests/2.28.1',
    'scrapy/2.5.1',
    'curl/7.68.0',
    'wget/1.20.3'
]

for agent in suspicious_agents:
    try:
        response = requests.get(url, headers={'User-Agent': agent})
        print(f"User-Agent '{agent}': Status {response.status_code}")
    except Exception as e:
        print(f"User-Agent '{agent}': Error - {e}")

print("\n" + "=" * 50)
print("Test completed!")
