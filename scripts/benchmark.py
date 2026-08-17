"""
PRGI Title Verification Benchmark & Diagnostic Verification Script
Tests accuracy across:
1. Prohibited non-text symbols & math characters (+, *, #, emojis) (Stage 1)
2. Numeric-only titles (just numbers) (Stage 1)
3. Pure generic combinations (Stage 1)
4. Disallowed keywords & Emblems Act (Stage 2)
5. Frankentitles (Stage 3)
6. Phonetic clones (Stage 4A)
7. Orthographic typos & reorderings (Stage 4B)
8. Cross-lingual semantic equivalents (Stage 4C)
9. Novel approved titles
10. Pending application lock collision
"""

import sys
import time
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from backend.data_loader import TitleIndex
from backend.lock_manager import LockManager
from backend.pipeline.engine import TitleVerificationEngine

BENCHMARK_TEST_CASES = [
    # 1. Prohibited non-text symbols & mathematical characters (Stage 1)
    {
        "title": "News+",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 1 (Prohibited Math Symbol '+')"
    },
    {
        "title": "Daily*Express",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 1 (Prohibited Symbol '*')"
    },
    {
        "title": "Star #1",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 1 (Prohibited Sign '#')"
    },

    # 2. Purely numeric titles (just numbers) (Stage 1)
    {
        "title": "2024",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 1 (Numeric-Only Title '2024')"
    },
    {
        "title": "12345",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 1 (Numeric-Only Title '12345')"
    },
    {
        "title": "24 7",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 1 (Numeric-Only Title '24 7')"
    },

    # 3. Pure generic rejection test cases (Stage 1)
    {
        "title": "The Daily News",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 1 (Pure Generic)"
    },
    {
        "title": "Weekly Express India",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 1 (Pure Generic)"
    },
    
    # 4. PRGI Guideline Blacklist violations (Stage 2)
    {
        "title": "The Crime Investigation Daily",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 2 (Disallowed Words - Crime)"
    },
    {
        "title": "Mumbai Police Chronicle",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 2 (Disallowed Words - Police)"
    },
    {
        "title": "National CBI Gazette",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 2 (Disallowed Words - CBI)"
    },
    {
        "title": "Delhi Sarkar Times",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 2 (Disallowed Words - Sarkar)"
    },
    {
        "title": "Ashoka Chakra Herald",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 2 (National Emblems Act)"
    },

    # 5. Frankentitle compound titles (Stage 3)
    {
        "title": "Hindu Indian Express",
        "expected_status": "Rejected",
        "expected_prob": 0.0,
        "category": "Stage 3 (Frankentitle Combination)"
    },

    # 6. Phonetic similarity tests (Stage 4A)
    {
        "title": "Namascar India",
        "expected_status": "Rejected",
        "expected_prob_max": 25.0,
        "category": "Stage 4A (Phonetic Homophone - Namaskar)"
    },
    {
        "title": "Daineq Bhaskar",
        "expected_status": "Rejected",
        "expected_prob_max": 25.0,
        "category": "Stage 4A (Phonetic Homophone - Dainik)"
    },

    # 7. Orthographic / Typo tests (Stage 4B)
    {
        "title": "The Tymes of India",
        "expected_status": "Rejected",
        "expected_prob_max": 35.0,
        "category": "Stage 4B (Orthographic Typo - Times)"
    },
    {
        "title": "Hindustan Tymes",
        "expected_status": "Rejected",
        "expected_prob_max": 35.0,
        "category": "Stage 4B (Orthographic Typo - Hindustan)"
    },

    # 8. Cross-Lingual Semantic Equivalence (Stage 4C)
    {
        "title": "Daily Evening",
        "expected_status": "Rejected",
        "expected_prob_max": 25.0,
        "category": "Stage 4C (Cross-Lingual - Pratidin Sandhya)"
    },
    {
        "title": "Morning News",
        "expected_status": "Rejected",
        "expected_prob_max": 25.0,
        "category": "Stage 4C (Cross-Lingual - Prabhat Samachar)"
    },
    {
        "title": "People's Voice",
        "expected_status": "Rejected",
        "expected_prob_max": 25.0,
        "category": "Stage 4C (Cross-Lingual - Jan Vani)"
    },
    {
        "title": "Truth Mirror",
        "expected_status": "Rejected",
        "expected_prob_max": 25.0,
        "category": "Stage 4C (Cross-Lingual - Satya Darpan)"
    },
    {
        "title": "Sakala Sambad",
        "expected_status": "Rejected",
        "expected_prob_max": 25.0,
        "category": "Stage 4C (Regional - Morning News)"
    },

    # 9. Novel distinctive titles (Should be Approved with high probability)
    {
        "title": "Zylophonic Quantum Astroflora",
        "expected_status": "Approved",
        "expected_prob_min": 60.0,
        "category": "Eligible / Novel Distinctive Title"
    },
    {
        "title": "Aurora Nebula Post",
        "expected_status": "Approved",
        "expected_prob_min": 60.0,
        "category": "Eligible / Novel Compound Title"
    }
]


def run_benchmark():
    print("=" * 75)
    print("PRGI Title Verification Engine - Comprehensive Diagnostic Benchmark")
    print("=" * 75)
    
    # 1. Initialize Index & Engine
    idx = TitleIndex()
    idx.load_data()
    
    lock_mgr = LockManager()
    engine = TitleVerificationEngine(titles_index=idx, lock_manager=lock_mgr)
    
    total_tests = len(BENCHMARK_TEST_CASES)
    passed_tests = 0
    total_latency_ms = 0.0
    
    print(f"\nRunning {total_tests} test cases across all verification stages:\n")
    print(f"{'Category':<38} | {'Submitted Title':<30} | {'Status':<10} | {'Prob':<6} | {'Time (ms)':<9} | {'Result'}")
    print("-" * 110)
    
    for tc in BENCHMARK_TEST_CASES:
        res = engine.verify_title(tc["title"])
        latency = res["execution_time_ms"]
        total_latency_ms += latency
        
        status_ok = (res["status"] == tc["expected_status"])
        prob_ok = True
        
        if "expected_prob" in tc:
            prob_ok = (res["verification_probability"] == tc["expected_prob"])
        if "expected_prob_max" in tc:
            prob_ok = prob_ok and (res["verification_probability"] <= tc["expected_prob_max"])
        if "expected_prob_min" in tc:
            prob_ok = prob_ok and (res["verification_probability"] >= tc["expected_prob_min"])
            
        test_passed = status_ok and prob_ok
        if test_passed:
            passed_tests += 1
            result_str = "[PASS] OK"
        else:
            result_str = f"[FAIL] Got {res['status']} ({res['verification_probability']}%)"
            
        print(f"{tc['category'][:38]:<38} | {tc['title'][:30]:<30} | {res['status']:<10} | {str(res['verification_probability'])+'%':<6} | {latency:<9.2f} | {result_str}")

    # 10. Pending Lock Concurrency Collision Test
    print("-" * 110)
    print("\nTesting Concurrency Lock Conflict (Pending Application Lock):")
    lock_title = "Sunrise Orbit Post"
    print(f"-> User A applying for '{lock_title}' with 600s lock...")
    ok_a, msg_a, _ = lock_mgr.acquire_lock(lock_title, applicant_id="USER_A", applicant_name="Applicant Alpha")
    print(f"   User A result: Acquired = {ok_a}")
    
    print(f"-> User B verifying '{lock_title}' 5 seconds later...")
    res_b = engine.verify_title(lock_title, applicant_id="USER_B")
    print(f"   User B verification status: {res_b['status']} | Probability: {res_b['verification_probability']}%")
    print(f"   Diagnostic Reason: {res_b['reasons'][0]['explanation']}")
    
    lock_test_passed = (res_b["status"] == "Rejected" and res_b["verification_probability"] == 0.0)
    if lock_test_passed:
        passed_tests += 1
        print("   Result: [PASS] OK")
    else:
        print("   Result: [FAIL]")
    total_tests += 1

    # Cleanup test lock
    lock_mgr.release_lock(lock_title, "USER_A")

    avg_latency = round(total_latency_ms / (total_tests - 1), 2)
    print("\n" + "=" * 75)
    print(f"BENCHMARK RESULTS: {passed_tests}/{total_tests} Tests Passed ({(passed_tests/total_tests)*100:.1f}%)")
    print(f"Average Engine Latency: {avg_latency} ms per query")
    print(f"Total Registered Titles Indexed: {idx.get_total_count()}")
    print("=" * 75)


if __name__ == "__main__":
    run_benchmark()
