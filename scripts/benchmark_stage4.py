"""
Stage 4 Performance & Latency Benchmarking Script

Measures empirical execution latencies across:
- Stage 4A (Phonetic Similarity Engine)
- Stage 4B (Orthographic Similarity Engine)
- Stage 4C (Cross-Lingual Semantic Engine)
- Unified Stage 4 Candidate Pair Comparison
- End-to-End Candidate Ranking over Index Retrieval (100 candidates)

Computes statistical distribution: Mean, Median (p50), 95th percentile (p95), 99th percentile (p99).
"""

import statistics
import sys
import time
from pathlib import Path
from typing import List

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.data_loader import TitleIndex
from backend.pipeline.stage1_preprocessor import extract_anchor_words
from backend.pipeline.stage4_integration import compare_title_against_candidate
from backend.pipeline.stage4_orthographic import compute_orthographic_similarity
from backend.pipeline.stage4_phonetic import compare_phonetic_similarity_detailed
from backend.pipeline.stage4_semantic import SemanticSimilarityEngine

# Representative sample pairs for realistic evaluation
BENCHMARK_PAIRS = [
    ("The Times of India", "The Tymes of India"),
    ("Dainik Jagran", "Daineq Jagran"),
    ("Namaskar Express", "Namascar Express"),
    ("Daily Evening", "Pratidin Sandhya"),
    ("Morning News", "Prabhat Samachar"),
    ("People's Voice", "Jan Vani"),
    ("Maharashtra Times", "Gujarat Samachar"),
    ("Quantum Physics Review", "Kisan Vani"),
    ("Solar Energy Digest", "Surya Urja Sangrah"),
    ("National Herald", "Rashtriya Doot"),
    ("Bat Sports Bulletin", "Bet Gaming Weekly"),
    ("Aurora Nebula Post", "Arawali Post"),
    ("Hindustan Times", "Hindustan Tymes"),
    ("Bharat Samachar", "Bhaarat Samachar"),
    ("Prabhat Samachar", "Sakala Sambad"),
    ("Pratidin Sandhya", "Rozana Shaam")
]


def percentile(data: List[float], p: float) -> float:
    """Compute exact percentile value."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_data) - 1)
    d = k - f
    return sorted_data[f] + d * (sorted_data[c] - sorted_data[f])


def run_benchmark(iterations_per_pair: int = 200):
    print("=" * 70)
    print("  PRGI Stage 4 Performance & Latency Benchmark")
    print("=" * 70)
    print(f"Sample pairs: {len(BENCHMARK_PAIRS)}")
    print(f"Iterations per pair: {iterations_per_pair}")
    print(f"Total pair evaluations per stage: {len(BENCHMARK_PAIRS) * iterations_per_pair}\n")

    semantic_engine = SemanticSimilarityEngine()

    latencies_4a_ms: List[float] = []
    latencies_4b_ms: List[float] = []
    latencies_4c_ms: List[float] = []
    latencies_stage4_ms: List[float] = []

    # Warm-up run
    for t1, t2 in BENCHMARK_PAIRS[:3]:
        compare_phonetic_similarity_detailed(t1, t2)
        compute_orthographic_similarity(t1, t2)
        semantic_engine.compare_semantic_similarity(t1, t2)
        compare_title_against_candidate(t1, t2, semantic_engine=semantic_engine)

    # 1. Benchmark Stage 4A (Phonetic)
    for _ in range(iterations_per_pair):
        for t1, t2 in BENCHMARK_PAIRS:
            t_start = time.perf_counter()
            compare_phonetic_similarity_detailed(t1, t2)
            latencies_4a_ms.append((time.perf_counter() - t_start) * 1000.0)

    # 2. Benchmark Stage 4B (Orthographic)
    for _ in range(iterations_per_pair):
        for t1, t2 in BENCHMARK_PAIRS:
            t_start = time.perf_counter()
            compute_orthographic_similarity(t1, t2)
            latencies_4b_ms.append((time.perf_counter() - t_start) * 1000.0)

    # 3. Benchmark Stage 4C (Semantic)
    for _ in range(iterations_per_pair):
        for t1, t2 in BENCHMARK_PAIRS:
            t_start = time.perf_counter()
            semantic_engine.compare_semantic_similarity(t1, t2)
            latencies_4c_ms.append((time.perf_counter() - t_start) * 1000.0)

    # 4. Benchmark Unified Stage 4 Pair Comparison
    for _ in range(iterations_per_pair):
        for t1, t2 in BENCHMARK_PAIRS:
            t_start = time.perf_counter()
            compare_title_against_candidate(t1, t2, semantic_engine=semantic_engine)
            latencies_stage4_ms.append((time.perf_counter() - t_start) * 1000.0)

    # 5. Benchmark Candidate Retrieval + Stage 4 Ranking (100 candidates)
    print("Loading TitleIndex dataset for Candidate Retrieval + Ranking Benchmark...")
    index = TitleIndex()
    index.load_data()
    
    latencies_candidate_ranking_ms: List[float] = []
    test_queries = [
        "Namaskar Times", "Daily Evening", "Morning News", "Hindustan Times",
        "Punjab Kesari", "Bharat Samachar", "Jan Vani", "Solar Science"
    ]
    
    for _ in range(25):
        for q in test_queries:
            t_start = time.perf_counter()
            s1 = extract_anchor_words(q)
            cands = index.find_candidates(s1["cleaned_title"], s1["anchor_words"], limit=100)
            for c in cands:
                compare_title_against_candidate(
                    s1["cleaned_title"],
                    c.get("cleaned_title", ""),
                    s1["anchor_words"],
                    c.get("anchor_words", ""),
                    semantic_engine=semantic_engine
                )
            latencies_candidate_ranking_ms.append((time.perf_counter() - t_start) * 1000.0)

    def print_stage_stats(name: str, latencies: List[float]):
        avg = statistics.mean(latencies)
        med = statistics.median(latencies)
        p95 = percentile(latencies, 95)
        p99 = percentile(latencies, 99)
        print(f"| {name:<36} | {avg:>8.4f} ms | {med:>8.4f} ms | {p95:>8.4f} ms | {p99:>8.4f} ms |")

    print("\n" + "=" * 80)
    print(f"| {'Component / Pipeline Step':<36} | {'Mean':>11} | {'Median':>11} | {'p95':>11} | {'p99':>11} |")
    print("=" * 80)
    print_stage_stats("Stage 4A: Phonetic (Double Metaphone)", latencies_4a_ms)
    print_stage_stats("Stage 4B: Orthographic (Lev/JW/3-Gram)", latencies_4b_ms)
    print_stage_stats("Stage 4C: Cross-Lingual Semantic", latencies_4c_ms)
    print_stage_stats("Unified Stage 4 Pair Comparison", latencies_stage4_ms)
    print_stage_stats("Full 100-Cand Retrieve & Rank", latencies_candidate_ranking_ms)
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()
