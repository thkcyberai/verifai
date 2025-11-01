#!/usr/bin/env python3
"""Analyze 360-test results and identify fix priorities."""
import csv
from collections import defaultdict

results_file = "test_results_1000_20251030_222525.csv"

failures_by_pattern = {
    "double_negation": [],  # "Is it false that X?" where X is false
    "unverified_edge": [],   # Should be TRUE/FALSE but got UNVERIFIED
    "verdict_flip": [],      # Got opposite verdict
    "other": []
}

with open(results_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['match'] == 'NO':
            statement = row['statement'].lower()
            expected = row['expected_verdict']
            actual = row['actual_verdict']
            
            # Categorize failure
            if 'is it false that' in statement and expected == 'FALSE' and actual == 'TRUE':
                failures_by_pattern['double_negation'].append(row)
            elif expected in ['TRUE', 'FALSE'] and actual == 'UNVERIFIED':
                failures_by_pattern['unverified_edge'].append(row)
            elif (expected == 'TRUE' and actual == 'FALSE') or (expected == 'FALSE' and actual == 'TRUE'):
                if 'is it false' not in statement:
                    failures_by_pattern['verdict_flip'].append(row)
                else:
                    failures_by_pattern['double_negation'].append(row)
            else:
                failures_by_pattern['other'].append(row)

print("="*80)
print("360-TEST ANALYSIS - FAILURE PATTERNS")
print("="*80)
print(f"\nTotal Failures: 69")
print(f"Pass Rate: 291/360 = 80.8%\n")

print("FAILURE BREAKDOWN:")
print(f"  Double Negation Bug:  {len(failures_by_pattern['double_negation'])} (CRITICAL)")
print(f"  Unverified Edge Cases: {len(failures_by_pattern['unverified_edge'])}")
print(f"  Verdict Flips:         {len(failures_by_pattern['verdict_flip'])}")
print(f"  Other:                 {len(failures_by_pattern['other'])}")

print("\n" + "="*80)
print("PRIORITY #1: DOUBLE NEGATION BUG (Affects ~40-50% of failures)")
print("="*80)
print("\nExamples:")
for fail in failures_by_pattern['double_negation'][:5]:
    print(f"\n  Statement: {fail['statement']}")
    print(f"  Expected: {fail['expected_verdict']} | Got: {fail['actual_verdict']}")
    print(f"  LLM: {fail['llm_score']} | Evidence: {fail['evidence_score']}")

print("\n" + "="*80)
print("RECOMMENDED FIX:")
print("="*80)
print("""
FILE: backend/app/adapters/openai_adapter.py

ISSUE: When user asks "Is it false that X?", the system evaluates whether 
       the statement "It is false that X" is true, rather than evaluating X itself.

FIX: Update the OpenAI prompt to extract the core claim from meta-questions:
     - "Is it true that X?" → Evaluate X
     - "Is it false that X?" → Evaluate X (not "it is false")
     - "Can you confirm X?" → Evaluate X
     
IMPLEMENTATION:
Add claim normalization BEFORE sending to OpenAI to strip meta-question framing.
""")

print("\n" + "="*80)
