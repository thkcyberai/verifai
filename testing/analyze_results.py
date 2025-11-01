#!/usr/bin/env python3
"""
VerifAI Test Results Analyzer
Analyzes test failures and generates actionable fix recommendations.
"""
import csv
from collections import defaultdict
from typing import Dict, List, Tuple


class FailureAnalyzer:
    def __init__(self, results_file: str = "test_results.csv"):
        self.results_file = results_file
        self.failures = []
        self.passes = []
        self.analysis = {
            "threshold_issues": [],
            "negation_failures": [],
            "logic_reasoning_errors": [],
            "search_pollution": [],
            "fusion_weight_issues": [],
            "confidence_issues": []
        }
        self.recommendations = []
    
    def load_results(self) -> List[Dict]:
        """Load test results from CSV."""
        results = []
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    results.append(row)
            
            # Separate passes and failures
            for result in results:
                if result["match"] == "NO":
                    self.failures.append(result)
                else:
                    self.passes.append(result)
            
            print(f"✅ Loaded {len(results)} test results")
            print(f"   Passed: {len(self.passes)}")
            print(f"   Failed: {len(self.failures)}")
            return results
        except FileNotFoundError:
            print(f"❌ Error: {self.results_file} not found!")
            return []
    
    def parse_score(self, score_str: str) -> float:
        """Parse score string to float."""
        try:
            return float(score_str)
        except (ValueError, TypeError):
            return 0.5
    
    def analyze_threshold_issues(self):
        """Analyze failures related to threshold boundaries."""
        for failure in self.failures:
            raw_score = self.parse_score(failure.get("raw_score", "0.5"))
            expected = failure["expected_verdict"]
            actual = failure["actual_verdict"]
            
            # Check if score is near threshold boundaries
            if expected == "FALSE" and 0.25 <= raw_score <= 0.35:
                self.analysis["threshold_issues"].append({
                    "test_id": failure["test_id"],
                    "statement": failure["statement"][:60],
                    "raw_score": raw_score,
                    "expected": expected,
                    "actual": actual,
                    "issue": f"Score {raw_score:.3f} near FALSE threshold (0.30)"
                })
            elif expected == "TRUE" and 0.65 <= raw_score <= 0.75:
                self.analysis["threshold_issues"].append({
                    "test_id": failure["test_id"],
                    "statement": failure["statement"][:60],
                    "raw_score": raw_score,
                    "expected": expected,
                    "actual": actual,
                    "issue": f"Score {raw_score:.3f} near TRUE threshold (0.70)"
                })
    
    def analyze_negation_failures(self):
        """Analyze failures related to negation detection."""
        negation_keywords = ["no", "not", "never", "doesn't", "don't", "didn't"]
        
        for failure in self.failures:
            statement = failure["statement"].lower()
            expected = failure["expected_verdict"]
            
            # Check if statement contains negation and expected FALSE
            has_negation = any(kw in statement for kw in negation_keywords)
            if has_negation and expected == "FALSE":
                evidence_score = self.parse_score(failure.get("evidence_score", "0.5"))
                
                # If evidence score is too high despite negation
                if evidence_score > 0.5:
                    self.analysis["negation_failures"].append({
                        "test_id": failure["test_id"],
                        "statement": failure["statement"][:60],
                        "evidence_score": evidence_score,
                        "issue": "Search didn't detect negation properly"
                    })
    
    def analyze_logic_reasoning(self):
        """Analyze failures in logic/reasoning claims."""
        for failure in self.failures:
            if failure["category"] == "Logic_Reasoning":
                llm_score = self.parse_score(failure.get("llm_score", "0.5"))
                evidence_score = self.parse_score(failure.get("evidence_score", "0.5"))
                
                self.analysis["logic_reasoning_errors"].append({
                    "test_id": failure["test_id"],
                    "statement": failure["statement"][:60],
                    "expected": failure["expected_verdict"],
                    "actual": failure["actual_verdict"],
                    "llm_score": llm_score,
                    "evidence_score": evidence_score,
                    "issue": "LLM or fusion failed on logic problem"
                })
    
    def analyze_search_pollution(self):
        """Analyze failures where irrelevant search results may have interfered."""
        for failure in self.failures:
            llm_score = self.parse_score(failure.get("llm_score", "0.5"))
            evidence_score = self.parse_score(failure.get("evidence_score", "0.5"))
            expected = failure["expected_verdict"]
            
            # LLM was correct but evidence pulled it wrong direction
            if expected == "FALSE" and llm_score < 0.3 and evidence_score > 0.6:
                self.analysis["search_pollution"].append({
                    "test_id": failure["test_id"],
                    "statement": failure["statement"][:60],
                    "llm_score": llm_score,
                    "evidence_score": evidence_score,
                    "issue": "Irrelevant search results contradicted correct LLM analysis"
                })
            elif expected == "TRUE" and llm_score > 0.7 and evidence_score < 0.4:
                self.analysis["search_pollution"].append({
                    "test_id": failure["test_id"],
                    "statement": failure["statement"][:60],
                    "llm_score": llm_score,
                    "evidence_score": evidence_score,
                    "issue": "Irrelevant search results contradicted correct LLM analysis"
                })
    
    def analyze_fusion_weights(self):
        """Analyze if fusion weights need adjustment."""
        for failure in self.failures:
            llm_score = self.parse_score(failure.get("llm_score", "0.5"))
            evidence_score = self.parse_score(failure.get("evidence_score", "0.5"))
            expected = failure["expected_verdict"]
            actual = failure["actual_verdict"]
            
            # LLM was very confident and correct, but fusion overruled it
            confidence_str = failure.get("confidence", "0%").replace("%", "")
            try:
                confidence = float(confidence_str) / 100
            except:
                confidence = 0.5
            
            if expected == "FALSE" and llm_score < 0.2 and actual != "FALSE":
                self.analysis["fusion_weight_issues"].append({
                    "test_id": failure["test_id"],
                    "statement": failure["statement"][:60],
                    "llm_score": llm_score,
                    "evidence_score": evidence_score,
                    "issue": "LLM was strongly correct but fusion didn't trust it enough"
                })
            elif expected == "TRUE" and llm_score > 0.8 and actual != "TRUE":
                self.analysis["fusion_weight_issues"].append({
                    "test_id": failure["test_id"],
                    "statement": failure["statement"][:60],
                    "llm_score": llm_score,
                    "evidence_score": evidence_score,
                    "issue": "LLM was strongly correct but fusion didn't trust it enough"
                })
    
    def generate_recommendations(self):
        """Generate specific, actionable fix recommendations."""
        fixes = []
        
        # Threshold adjustments
        if len(self.analysis["threshold_issues"]) > 5:
            false_boundary = [f for f in self.analysis["threshold_issues"] if f["expected"] == "FALSE"]
            true_boundary = [f for f in self.analysis["threshold_issues"] if f["expected"] == "TRUE"]
            
            if len(false_boundary) > 2:
                avg_score = sum(f["raw_score"] for f in false_boundary) / len(false_boundary)
                fixes.append({
                    "priority": "HIGH",
                    "category": "Threshold Adjustment",
                    "affected_tests": len(false_boundary),
                    "issue": f"{len(false_boundary)} FALSE claims scoring near 0.30 threshold",
                    "fix": f"Increase FALSE_THRESHOLD from 0.30 to {avg_score + 0.05:.2f}",
                    "file": "backend/app/fusion/engine.py",
                    "line": "FALSE_THRESHOLD = 0.30"
                })
            
            if len(true_boundary) > 2:
                avg_score = sum(f["raw_score"] for f in true_boundary) / len(true_boundary)
                fixes.append({
                    "priority": "HIGH",
                    "category": "Threshold Adjustment",
                    "affected_tests": len(true_boundary),
                    "issue": f"{len(true_boundary)} TRUE claims scoring near 0.70 threshold",
                    "fix": f"Decrease TRUE_THRESHOLD from 0.70 to {avg_score - 0.05:.2f}",
                    "file": "backend/app/fusion/engine.py",
                    "line": "TRUE_THRESHOLD = 0.70"
                })
        
        # Negation detection
        if len(self.analysis["negation_failures"]) > 3:
            fixes.append({
                "priority": "HIGH",
                "category": "Search Adapter - Negation",
                "affected_tests": len(self.analysis["negation_failures"]),
                "issue": f"{len(self.analysis['negation_failures'])} claims with negation not detected properly",
                "fix": "Add more negation patterns to search_adapter.py negation_patterns list",
                "file": "backend/app/adapters/search_adapter.py",
                "code_snippet": """negation_patterns = [
    r'\\bno\\s+(link|connection|evidence|relationship)',
    r'\\bdo\\s+not\\s+cause\\b',
    r'\\bshows\\s+no\\b',
    # ADD MORE PATTERNS HERE
]"""
            })
        
        # Logic reasoning
        if len(self.analysis["logic_reasoning_errors"]) > 5:
            fixes.append({
                "priority": "MEDIUM",
                "category": "LLM Confidence Override",
                "affected_tests": len(self.analysis["logic_reasoning_errors"]),
                "issue": f"{len(self.analysis['logic_reasoning_errors'])} logic problems failed",
                "fix": "Consider lowering high_confidence_llm threshold from 0.90 to 0.85 for logic claims",
                "file": "backend/app/fusion/engine.py",
                "line": "if llm_confidence and llm_confidence >= 0.90"
            })
        
        # Search pollution
        if len(self.analysis["search_pollution"]) > 5:
            fixes.append({
                "priority": "MEDIUM",
                "category": "Search Quality Filter",
                "affected_tests": len(self.analysis["search_pollution"]),
                "issue": f"{len(self.analysis['search_pollution'])} claims affected by irrelevant search results",
                "fix": "Add relevance scoring to filter out off-topic search results",
                "file": "backend/app/adapters/search_adapter.py",
                "suggestion": "Calculate keyword overlap between claim and result, discard results below threshold"
            })
        
        # Fusion weight issues
        if len(self.analysis["fusion_weight_issues"]) > 5:
            fixes.append({
                "priority": "LOW",
                "category": "Fusion Weights",
                "affected_tests": len(self.analysis["fusion_weight_issues"]),
                "issue": f"{len(self.analysis['fusion_weight_issues'])} claims where LLM was right but overruled",
                "fix": "Increase LLM weight from 0.20 to 0.25, decrease evidence from 0.35 to 0.30",
                "file": "backend/app/fusion/engine.py",
                "line": "WEIGHTS = {'media_forensics': 0.45, 'evidence': 0.35, 'llm_reasoning': 0.20}"
            })
        
        self.recommendations = sorted(fixes, key=lambda x: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["priority"]],
            -x["affected_tests"]
        ))
    
    def print_analysis_report(self):
        """Print detailed analysis report."""
        print("\n" + "="*80)
        print("VERIFAI TEST FAILURE ANALYSIS REPORT")
        print("="*80)
        
        print(f"\nTotal Failures: {len(self.failures)}")
        
        # Threshold issues
        if self.analysis["threshold_issues"]:
            print(f"\n📊 THRESHOLD BOUNDARY ISSUES: {len(self.analysis['threshold_issues'])}")
            for issue in self.analysis["threshold_issues"][:3]:
                print(f"   Test #{issue['test_id']}: {issue['statement']}...")
                print(f"   Score: {issue['raw_score']:.3f} | {issue['issue']}")
        
        # Negation failures
        if self.analysis["negation_failures"]:
            print(f"\n🔍 NEGATION DETECTION FAILURES: {len(self.analysis['negation_failures'])}")
            for issue in self.analysis["negation_failures"][:3]:
                print(f"   Test #{issue['test_id']}: {issue['statement']}...")
                print(f"   Evidence Score: {issue['evidence_score']:.2f} | {issue['issue']}")
        
        # Logic reasoning
        if self.analysis["logic_reasoning_errors"]:
            print(f"\n🧠 LOGIC REASONING ERRORS: {len(self.analysis['logic_reasoning_errors'])}")
            for issue in self.analysis["logic_reasoning_errors"][:3]:
                print(f"   Test #{issue['test_id']}: {issue['statement']}...")
                print(f"   Expected: {issue['expected']} | Actual: {issue['actual']}")
                print(f"   LLM: {issue['llm_score']:.2f} | Evidence: {issue['evidence_score']:.2f}")
        
        # Search pollution
        if self.analysis["search_pollution"]:
            print(f"\n🌐 SEARCH POLLUTION: {len(self.analysis['search_pollution'])}")
            for issue in self.analysis["search_pollution"][:3]:
                print(f"   Test #{issue['test_id']}: {issue['statement']}...")
                print(f"   LLM: {issue['llm_score']:.2f} | Evidence: {issue['evidence_score']:.2f}")
                print(f"   {issue['issue']}")
        
        # Fusion weight issues
        if self.analysis["fusion_weight_issues"]:
            print(f"\n⚖️  FUSION WEIGHT ISSUES: {len(self.analysis['fusion_weight_issues'])}")
            for issue in self.analysis["fusion_weight_issues"][:3]:
                print(f"   Test #{issue['test_id']}: {issue['statement']}...")
                print(f"   {issue['issue']}")
        
        print("\n" + "="*80)
    
    def print_recommendations(self):
        """Print prioritized fix recommendations."""
        print("\n" + "="*80)
        print("PRIORITIZED FIX RECOMMENDATIONS")
        print("="*80)
        
        if not self.recommendations:
            print("\n✅ No systemic issues found! Manual review of individual failures recommended.")
            return
        
        for i, rec in enumerate(self.recommendations, 1):
            print(f"\n[{rec['priority']}] FIX #{i}: {rec['category']}")
            print(f"{'─'*80}")
            print(f"Affected Tests: {rec['affected_tests']}")
            print(f"Issue: {rec['issue']}")
            print(f"\n✨ RECOMMENDED FIX:")
            print(f"   {rec['fix']}")
            print(f"\n📁 File: {rec['file']}")
            if "line" in rec:
                print(f"📍 Line: {rec['line']}")
            if "code_snippet" in rec:
                print(f"\n💻 Code:")
                print(f"{rec['code_snippet']}")
            if "suggestion" in rec:
                print(f"\n💡 Suggestion: {rec['suggestion']}")
        
        print("\n" + "="*80)
        print("\n🎯 NEXT STEPS:")
        print("1. Review and implement HIGH priority fixes first")
        print("2. Re-run tests: python run_tests.py")
        print("3. Re-analyze results: python analyze_results.py")
        print("4. Iterate until desired accuracy achieved")
        print("="*80)
    
    def run_analysis(self):
        """Run complete analysis."""
        print("\n🔬 Starting VerifAI Test Results Analysis...\n")
        
        # Load results
        if not self.load_results():
            return
        
        if not self.failures:
            print("\n🎉 All tests passed! No failures to analyze.")
            return
        
        # Run analyses
        print("\n⚙️  Analyzing failure patterns...")
        self.analyze_threshold_issues()
        self.analyze_negation_failures()
        self.analyze_logic_reasoning()
        self.analyze_search_pollution()
        self.analyze_fusion_weights()
        
        # Generate recommendations
        print("⚙️  Generating fix recommendations...")
        self.generate_recommendations()
        
        # Print reports
        self.print_analysis_report()
        self.print_recommendations()


if __name__ == "__main__":
    analyzer = FailureAnalyzer()
    analyzer.run_analysis()
