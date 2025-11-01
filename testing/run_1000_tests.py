#!/usr/bin/env python3
"""Run 1000 test suite - optimized for overnight execution."""
import csv
import requests
import time
from datetime import datetime
from typing import Dict, List

API_URL = "http://localhost:8000/api/v1/verify"
INPUT_FILE = "test_statements_1000.csv"
OUTPUT_FILE = f"test_results_1000_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
DELAY_BETWEEN_TESTS = 0.5  # Faster for 1000 tests

class VerifAITester:
    def __init__(self):
        self.results = []
        self.summary = {"total": 0, "passed": 0, "failed": 0, "errors": 0}
        self.start_time = None
    
    def load_test_statements(self) -> List[Dict]:
        statements = []
        try:
            with open(INPUT_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    statements.append(row)
            print(f"✅ Loaded {len(statements)} test statements")
            return statements
        except FileNotFoundError:
            print(f"❌ Error: {INPUT_FILE} not found!")
            return []
    
    def verify_claim(self, statement: str) -> Dict:
        try:
            payload = {"claim": statement}
            response = requests.post(API_URL, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "verdict": "ERROR"}
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "verdict": "ERROR"}
    
    def compare_verdicts(self, expected: str, actual: str) -> bool:
        return expected.upper() == actual.upper()
    
    def run_test(self, test: Dict, index: int, total: int) -> Dict:
        statement = test["statement"]
        expected = test["expected_verdict"]
        
        # Progress indicator every 50 tests
        if index % 50 == 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            rate = index / elapsed if elapsed > 0 else 0
            eta_seconds = (total - index) / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60
            print(f"\n[{index}/{total}] Progress: {index/total*100:.1f}% | Rate: {rate:.1f} tests/sec | ETA: {eta_minutes:.1f} min")
        
        result = self.verify_claim(statement)
        
        actual = result.get("verdict", "ERROR")
        confidence = result.get("confidence", 0)
        match = self.compare_verdicts(expected, actual) if actual != "ERROR" else False
        
        checks = result.get("checks", {})
        llm_score = checks.get("llm_reasoning_score")
        evidence_score = checks.get("evidence_score")
        
        if llm_score is not None and evidence_score is not None:
            raw_score = (llm_score * 0.20 + evidence_score * 0.35) / 0.55
        else:
            raw_score = 0.5
        
        self.summary["total"] += 1
        if actual == "ERROR":
            self.summary["errors"] += 1
        elif match:
            self.summary["passed"] += 1
        else:
            self.summary["failed"] += 1
        
        test_result = {
            "test_id": test["test_id"],
            "category": test["category"],
            "difficulty": test["difficulty"],
            "statement": statement,
            "expected_verdict": expected,
            "actual_verdict": actual,
            "confidence": f"{confidence:.1%}" if confidence else "N/A",
            "match": "YES" if match else "NO",
            "llm_score": f"{llm_score:.2f}" if llm_score is not None else "N/A",
            "evidence_score": f"{evidence_score:.2f}" if evidence_score is not None else "N/A",
            "raw_score": f"{raw_score:.3f}",
            "reasoning": test["reasoning"]
        }
        
        self.results.append(test_result)
        
        # Save checkpoint every 100 tests
        if index % 100 == 0:
            self.save_results()
        
        return test_result
    
    def save_results(self):
        if not self.results:
            return
        
        fieldnames = [
            "test_id", "category", "difficulty", "statement", 
            "expected_verdict", "actual_verdict", "confidence", "match",
            "llm_score", "evidence_score", "raw_score", "reasoning"
        ]
        
        try:
            with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def generate_report(self):
        print("\n" + "="*60)
        print("1000-TEST SUMMARY REPORT")
        print("="*60)
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"Duration:     {elapsed/60:.1f} minutes")
        print(f"Total Tests:  {self.summary['total']}")
        print(f"Passed:       {self.summary['passed']} ({self.summary['passed']/self.summary['total']*100:.1f}%)")
        print(f"Failed:       {self.summary['failed']} ({self.summary['failed']/self.summary['total']*100:.1f}%)")
        print(f"Errors:       {self.summary['errors']}")
        print("="*60)
        print(f"\n✅ Results saved to: {OUTPUT_FILE}")
    
    def run_all_tests(self):
        self.start_time = datetime.now()
        print("\n🚀 Starting 1000-Statement Test Suite")
        print(f"📅 {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("⏰ Estimated completion: ~15-20 minutes\n")
        
        statements = self.load_test_statements()
        if not statements:
            return
        
        total = len(statements)
        for i, test in enumerate(statements, 1):
            self.run_test(test, i, total)
            if i < total:
                time.sleep(DELAY_BETWEEN_TESTS)
        
        self.save_results()
        self.generate_report()


if __name__ == "__main__":
    tester = VerifAITester()
    tester.run_all_tests()
