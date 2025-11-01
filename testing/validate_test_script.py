#!/usr/bin/env python3
"""
Validate that the test script correctly records API responses.
"""
import requests
import json

API_URL = "http://localhost:8000/api/v1/verify"

# 5 test cases with obvious expected results
test_cases = [
    {"claim": "Water boils at 100 degrees Celsius at sea level", "expected": "TRUE"},
    {"claim": "The Earth is flat", "expected": "FALSE"},
    {"claim": "Paris is the capital of France", "expected": "TRUE"},
    {"claim": "The moon is made of cheese", "expected": "FALSE"},
    {"claim": "Aliens visit Earth regularly", "expected": "UNVERIFIED"}
]

print("\n" + "="*80)
print("VALIDATION TEST: Comparing API Response vs Expected")
print("="*80)

all_correct = True

for i, test in enumerate(test_cases, 1):
    print(f"\n[{i}/5] Testing: {test['claim']}")
    print("─"*80)
    
    # Call API
    response = requests.post(API_URL, json={"claim": test['claim']}, timeout=30)
    result = response.json()
    
    # Extract key data
    api_verdict = result.get("verdict", "ERROR")
    api_confidence = result.get("confidence", 0)
    checks = result.get("checks", {})
    llm_score = checks.get("llm_reasoning_score", None)
    evidence_score = checks.get("evidence_score", None)
    
    # Display
    print(f"Expected Verdict:  {test['expected']}")
    print(f"API Verdict:       {api_verdict}")
    print(f"Match:             {'✅ YES' if api_verdict == test['expected'] else '❌ NO'}")
    print(f"Confidence:        {api_confidence:.1%}")
    print(f"LLM Score:         {llm_score if llm_score else 'N/A'}")
    print(f"Evidence Score:    {evidence_score if evidence_score else 'N/A'}")
    
    if api_verdict != test['expected']:
        all_correct = False
        print(f"⚠️  API RETURNED UNEXPECTED VERDICT!")

print("\n" + "="*80)
if all_correct:
    print("✅ ALL 5 VALIDATION TESTS PASSED")
    print("✅ API is working correctly")
    print("✅ Safe to trust test results")
else:
    print("❌ SOME TESTS FAILED")
    print("❌ Need to investigate VerifAI logic before running full test suite")
print("="*80 + "\n")
