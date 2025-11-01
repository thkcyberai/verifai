#!/usr/bin/env python3
"""Review individual test failures in detail and save to file."""
import csv
from datetime import datetime

results_file = "test_results.csv"
output_file = f"failure_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

# Open output file
with open(output_file, 'w', encoding='utf-8') as out:
    def print_both(text):
        """Print to console and file."""
        print(text)
        out.write(text + "\n")
    
    print_both("="*80)
    print_both("DETAILED FAILURE REVIEW")
    print_both("="*80)
    print_both(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load results
    with open(results_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        results = list(reader)
        failures = [row for row in results if row["match"] == "NO"]
        passes = [row for row in results if row["match"] == "YES"]
    
    # Summary statistics
    print_both(f"\nTotal Tests: {len(results)}")
    print_both(f"Passed: {len(passes)} ({len(passes)/len(results)*100:.1f}%)")
    print_both(f"Failed: {len(failures)} ({len(failures)/len(results)*100:.1f}%)")
    
    # Breakdown by category
    category_stats = {}
    for result in results:
        cat = result['category']
        if cat not in category_stats:
            category_stats[cat] = {'total': 0, 'passed': 0, 'failed': 0}
        category_stats[cat]['total'] += 1
        if result['match'] == 'YES':
            category_stats[cat]['passed'] += 1
        else:
            category_stats[cat]['failed'] += 1
    
    print_both("\n" + "="*80)
    print_both("ACCURACY BY CATEGORY")
    print_both("="*80)
    for cat, stats in sorted(category_stats.items(), key=lambda x: x[1]['failed'], reverse=True):
        accuracy = stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print_both(f"{cat:20s}: {stats['passed']:3d}/{stats['total']:3d} ({accuracy:5.1f}%) | Failed: {stats['failed']}")
    
    print_both("\n" + "="*80)
    print_both("DETAILED FAILURE ANALYSIS")
    print_both("="*80 + "\n")
    
    for i, fail in enumerate(failures, 1):
        print_both(f"\n[{i}/{len(failures)}] TEST #{fail['test_id']} - {fail['category']} ({fail['difficulty']})")
        print_both("─"*80)
        print_both(f"Statement: {fail['statement']}")
        print_both(f"Expected: {fail['expected_verdict']:12s} | Actual: {fail['actual_verdict']:12s} | Confidence: {fail['confidence']}")
        print_both(f"LLM Score: {fail['llm_score']:6s} | Evidence: {fail['evidence_score']:6s} | Raw Score: {fail['raw_score']}")
        
        if fail['rules_triggered']:
            print_both(f"Rules Triggered: {fail['rules_triggered']}")
        
        print_both(f"Issue Type: {fail['issue_type']}")
        print_both(f"Reasoning: {fail['reasoning']}")
        
        # Provide quick diagnosis
        llm = fail['llm_score']
        evidence = fail['evidence_score']
        expected = fail['expected_verdict']
        actual = fail['actual_verdict']
        
        if llm == "N/A" or evidence == "N/A":
            print_both("⚠️  DIAGNOSIS: Missing score data - check API response")
        else:
            try:
                llm_f = float(llm)
                evid_f = float(evidence)
                raw_f = float(fail['raw_score'])
                
                # Detailed diagnosis
                if abs(llm_f - evid_f) > 0.3:
                    print_both(f"⚠️  DIAGNOSIS: LLM ({llm_f:.2f}) and Evidence ({evid_f:.2f}) strongly conflict")
                    if expected == "FALSE" and llm_f < 0.3 and evid_f > 0.5:
                        print_both(f"    → LLM correctly identified FALSE, but search results contradicted it")
                    elif expected == "TRUE" and llm_f > 0.7 and evid_f < 0.5:
                        print_both(f"    → LLM correctly identified TRUE, but search results contradicted it")
                elif 0.28 <= raw_f <= 0.32:
                    print_both(f"⚠️  DIAGNOSIS: Score ({raw_f:.3f}) very close to FALSE threshold (0.30)")
                    print_both(f"    → Consider adjusting threshold or weights")
                elif 0.68 <= raw_f <= 0.72:
                    print_both(f"⚠️  DIAGNOSIS: Score ({raw_f:.3f}) very close to TRUE threshold (0.70)")
                    print_both(f"    → Consider adjusting threshold or weights")
                else:
                    print_both(f"ℹ️  DIAGNOSIS: Scores aligned ({llm_f:.2f}, {evid_f:.2f}) but produced wrong verdict")
                    if fail['category'] == 'Logic_Reasoning':
                        print_both(f"    → GPT-4o struggled with this logic problem")
                    
            except ValueError:
                print_both("⚠️  DIAGNOSIS: Could not parse scores")
    
    print_both("\n" + "="*80)
    print_both("RECOMMENDATIONS")
    print_both("="*80)
    
    # Count issue types
    issue_counts = {}
    for fail in failures:
        issue = fail['issue_type']
        if issue:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    
    if issue_counts:
        print_both("\nFailure Distribution:")
        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            print_both(f"  {issue}: {count}")
    
    # Generic recommendations
    if len(failures) < 20:
        print_both("\n✅ Overall accuracy is good! Focus on individual edge cases.")
    else:
        print_both("\n⚠️  Significant failures detected. Review patterns and consider systemic fixes.")
    
    print_both("\n" + "="*80)

print(f"\n✅ Detailed report saved to: {output_file}")
