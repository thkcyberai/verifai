#!/usr/bin/env python3
"""Run 1000 statements 3 times each = 3000 total tests."""
import csv
import time
import requests
from datetime import datetime
from collections import defaultdict

API_URL = "http://localhost:8000/api/v1/verify"

def verify_claim(statement):
    """Send claim to VerifAI API."""
    try:
        response = requests.post(
            API_URL,
            json={"claim": statement},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return {
            "verdict": result.get("verdict"),
            "confidence": result.get("confidence"),
            "llm_score": result.get("fusion_details", {}).get("raw_score", 0.5),
            "evidence_score": result.get("evidence_score", 0.5),
            "reasoning": result.get("reasoning", "")
        }
    except Exception as e:
        print(f"    ⚠️  Error: {str(e)}")
        return None

def load_statements(filename):
    """Load test statements from CSV."""
    statements = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        statements = list(reader)
    return statements

def run_tests_with_repeats():
    """Run 1000 statements × 3 times each."""
    statements = load_statements('test_statements_1000.csv')
    print(f"✅ Loaded {len(statements)} test statements")
    print(f"🔄 Will run each statement 3 times = {len(statements) * 3} total tests")
    
    all_results = []
    test_counter = 0
    start_time = time.time()
    
    # Statistics tracking
    stats = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'errors': 0,
        'by_repeat': defaultdict(lambda: {'passed': 0, 'failed': 0}),
        'consistency': defaultdict(list)  # Track consistency across repeats
    }
    
    # Run each statement 3 times
    for repeat_num in range(1, 4):
        print(f"\n{'='*60}")
        print(f"REPEAT #{repeat_num}/3")
        print(f"{'='*60}")
        
        for idx, stmt in enumerate(statements, 1):
            test_counter += 1
            stats['total'] += 1
            
            # Progress update every 50 tests
            if test_counter % 50 == 0:
                elapsed = time.time() - start_time
                rate = test_counter / elapsed if elapsed > 0 else 0
                remaining = (len(statements) * 3 - test_counter) / rate if rate > 0 else 0
                print(f"[{test_counter}/{len(statements)*3}] Progress: {(test_counter/(len(statements)*3)*100):.1f}% | "
                      f"Rate: {rate:.1f} tests/sec | ETA: {remaining/60:.1f} min")
            
            # Run verification
            result = verify_claim(stmt['statement'])
            
            if result is None:
                stats['errors'] += 1
                continue
            
            # Check if verdict matches expected
            expected = stmt['expected_verdict']
            actual = result['verdict']
            match = "YES" if expected == actual else "NO"
            
            if match == "YES":
                stats['passed'] += 1
                stats['by_repeat'][repeat_num]['passed'] += 1
            else:
                stats['failed'] += 1
                stats['by_repeat'][repeat_num]['failed'] += 1
            
            # Track consistency
            stats['consistency'][stmt['test_id']].append(actual)
            
            # Save result
            all_results.append({
                'test_id': stmt['test_id'],
                'repeat': repeat_num,
                'global_test_num': test_counter,
                'category': stmt['category'],
                'difficulty': stmt['difficulty'],
                'statement': stmt['statement'],
                'expected_verdict': expected,
                'actual_verdict': actual,
                'confidence': f"{result['confidence']*100:.1f}%",
                'match': match,
                'llm_score': f"{result['llm_score']:.2f}",
                'evidence_score': f"{result['evidence_score']:.2f}",
                'reasoning': result['reasoning']
            })
    
    # Calculate consistency metrics
    consistency_perfect = 0
    consistency_2of3 = 0
    consistency_inconsistent = 0
    
    for test_id, verdicts in stats['consistency'].items():
        if len(set(verdicts)) == 1:
            consistency_perfect += 1
        elif len(verdicts) == 3:
            # Check if 2 out of 3 match
            from collections import Counter
            counts = Counter(verdicts)
            if max(counts.values()) >= 2:
                consistency_2of3 += 1
            else:
                consistency_inconsistent += 1
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'test_results_3000_{timestamp}.csv'
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['test_id', 'repeat', 'global_test_num', 'category', 'difficulty', 
                     'statement', 'expected_verdict', 'actual_verdict', 'confidence', 
                     'match', 'llm_score', 'evidence_score', 'reasoning']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    
    # Print summary
    duration = (time.time() - start_time) / 60
    print(f"\n{'='*60}")
    print("3000-TEST SUMMARY REPORT")
    print(f"{'='*60}")
    print(f"Duration:     {duration:.1f} minutes")
    print(f"Total Tests:  {stats['total']}")
    print(f"Passed:       {stats['passed']} ({stats['passed']/stats['total']*100:.1f}%)")
    print(f"Failed:       {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
    print(f"Errors:       {stats['errors']}")
    print(f"\nPER-REPEAT BREAKDOWN:")
    for repeat_num in range(1, 4):
        r = stats['by_repeat'][repeat_num]
        total_repeat = r['passed'] + r['failed']
        print(f"  Repeat #{repeat_num}: {r['passed']}/{total_repeat} passed ({r['passed']/total_repeat*100:.1f}%)")
    print(f"\nCONSISTENCY ANALYSIS (across 3 repeats):")
    print(f"  Perfect (3/3 same):   {consistency_perfect}/{len(statements)} ({consistency_perfect/len(statements)*100:.1f}%)")
    print(f"  Majority (2/3 same):  {consistency_2of3}/{len(statements)} ({consistency_2of3/len(statements)*100:.1f}%)")
    print(f"  Inconsistent:         {consistency_inconsistent}/{len(statements)} ({consistency_inconsistent/len(statements)*100:.1f}%)")
    print(f"{'='*60}")
    print(f"✅ Results saved to: {output_file}")
    
    return output_file

if __name__ == "__main__":
    run_tests_with_repeats()
