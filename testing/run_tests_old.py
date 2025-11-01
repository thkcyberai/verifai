#!/usr/bin/env python3
"""
Automated VerifAI Testing Script
Loads test statements, runs them through the API, and generates results report.
"""
import csv
import requests
import time
import json
from datetime import datetime
from typing import Dict, List

# Configuration
API_URL = "http://localhost:8000/api/v1/verify"
INPUT_FILE = "test_statements.csv"
OUTPUT_FILE = "test_results.csv"
DELAY_BETWEEN_TESTS = 1  # seconds between API calls


class VerifAITester:
    def __init__(self):
        self.results = []
        self.summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0
        }
    
    def load_test_statements(self) -> List[Dict]:
        """Load test statements from CSV."""
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
        """Call VerifAI API to verify a claim."""
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
        """Compare expected vs actual verdict."""
        return expected.upper() == actual.upper()
    
    def determine_issue_type(self, test: Dict, result: Dict) -> str:
        """Determine the type of issue when a test fails."""
        if result.get("verdict") == "ERROR":
            return "API_ERROR"
        
        expected = test["expected_verdict"].upper()
        actual = result.get("verdict", "").upper()
        confidence = result.get("confidence", 0)
        
        # Extract fusion details if available
        fusion = result.get("fusion_details", {})
        raw_score = fusion.get("raw_score", 0.5)
        
        # Categorize the issue
        if 0.25 <= raw_score <= 0.35 or 0.65 <= raw_score <= 0.75:
            return "THRESHOLD_BOUNDARY"
        elif expected in ["TRUE", "FALSE"] and actual == "UNVERIFIED":
            return "FUSION_INDECISIVE"
        elif test["difficulty"] == "Hard" and test["category"] == "Logic_Reasoning":
            return "LOGIC_REASONING_ERROR"
        elif confidence < 0.5:
            return "LOW_CONFIDENCE"
        else:
            return "VERDICT_MISMATCH"
    
    def run_test(self, test: Dict, index: int, total: int) -> Dict:
        """Run a single test case."""
        statement = test["statement"]
        expected = test["expected_verdict"]
        
        print(f"\n[{index}/{total}] Testing: {statement[:60]}...")
        print(f"  Expected: {expected}")
        
        # Call API
        result = self.verify_claim(statement)
        
        # Extract data
        actual = result.get("verdict", "ERROR")
        confidence = result.get("confidence", 0)
        match = self.compare_verdicts(expected, actual) if actual != "ERROR" else False
        
        # Get detailed scores from fusion_details
        fusion = result.get("fusion_details", {})
        llm_score = result.get("llm_analysis", {}).get("score", "N/A")
        evidence_score = result.get("evidence_analysis", {}).get("score", "N/A")
        raw_score = fusion.get("raw_score", "N/A")
        rules_triggered = ", ".join(fusion.get("rules_triggered", []))
        
        # Determine issue type if failed
        issue_type = "" if match else self.determine_issue_type(test, result)
        
        print(f"  Actual: {actual} ({confidence:.1%})")
        print(f"  Match: {'✅ PASS' if match else '❌ FAIL'}")
        
        # Update summary
        self.summary["total"] += 1
        if actual == "ERROR":
            self.summary["errors"] += 1
        elif match:
            self.summary["passed"] += 1
        else:
            self.summary["failed"] += 1
        
        # Build result record
        test_result = {
            "test_id": test["test_id"],
            "category": test["category"],
            "difficulty": test["difficulty"],
            "statement": statement,
            "expected_verdict": expected,
            "actual_verdict": actual,
            "confidence": f"{confidence:.1%}" if confidence else "N/A",
            "match": "YES" if match else "NO",
            "llm_score": f"{llm_score:.2f}" if isinstance(llm_score, (int, float)) else llm_score,
            "evidence_score": f"{evidence_score:.2f}" if isinstance(evidence_score, (int, float)) else evidence_score,
            "raw_score": f"{raw_score:.3f}" if isinstance(raw_score, (int, float)) else raw_score,
            "rules_triggered": rules_triggered,
            "issue_type": issue_type,
            "reasoning": test["reasoning"]
        }
        
        self.results.append(test_result)
        return test_result
    
    def save_results(self):
        """Save test results to CSV."""
        if not self.results:
            print("❌ No results to save!")
            return
        
        fieldnames = [
            "test_id", "category", "difficulty", "statement", 
            "expected_verdict", "actual_verdict", "confidence", "match",
            "llm_score", "evidence_score", "raw_score", "rules_triggered",
            "issue_type", "reasoning"
        ]
        
        try:
            with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
            print(f"\n✅ Results saved to {OUTPUT_FILE}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def generate_report(self):
        """Generate summary report."""
        print("\n" + "="*60)
        print("TEST SUMMARY REPORT")
        print("="*60)
        print(f"Total Tests:  {self.summary['total']}")
        print(f"Passed:       {self.summary['passed']} ({self.summary['passed']/self.summary['total']*100:.1f}%)")
        print(f"Failed:       {self.summary['failed']} ({self.summary['failed']/self.summary['total']*100:.1f}%)")
        print(f"Errors:       {self.summary['errors']}")
        print("="*60)
        
        # Breakdown by category
        if self.summary['failed'] > 0:
            print("\nFAILURES BY CATEGORY:")
            category_fails = {}
            for result in self.results:
                if result["match"] == "NO":
                    cat = result["category"]
                    category_fails[cat] = category_fails.get(cat, 0) + 1
            
            for cat, count in sorted(category_fails.items(), key=lambda x: x[1], reverse=True):
                print(f"  {cat}: {count}")
        
        # Breakdown by issue type
        if self.summary['failed'] > 0:
            print("\nFAILURES BY ISSUE TYPE:")
            issue_counts = {}
            for result in self.results:
                if result["match"] == "NO" and result["issue_type"]:
                    issue = result["issue_type"]
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {issue}: {count}")
        
        print("\n" + "="*60)
    
    def run_all_tests(self):
        """Main test execution."""
        print("\n🚀 Starting VerifAI Automated Testing")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Load statements
        statements = self.load_test_statements()
        if not statements:
            return
        
        # Run tests
        total = len(statements)
        for i, test in enumerate(statements, 1):
            self.run_test(test, i, total)
            
            # Delay between tests to avoid rate limiting
            if i < total:
                time.sleep(DELAY_BETWEEN_TESTS)
        
        # Save and report
        self.save_results()
        self.generate_report()


if __name__ == "__main__":
    tester = VerifAITester()
    tester.run_all_tests()
