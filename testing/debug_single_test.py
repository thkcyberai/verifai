#!/usr/bin/env python3
"""Debug a single test to see full API response."""
import requests
import json

API_URL = "http://localhost:8000/api/v1/verify"

# Test the failing claim
statement = "Ice melts at room temperature"

print(f"\n🔍 Testing: {statement}")
print("="*80)

response = requests.post(API_URL, json={"claim": statement}, timeout=30)

print(f"\nStatus Code: {response.status_code}")
print(f"\nFull API Response:")
print("="*80)
print(json.dumps(response.json(), indent=2))
print("="*80)
