"""
Stage 4 Accuracy & Diagnostic Evaluation Script

Evaluates Stage 4 similarity engine against the curated benchmark dataset:
- True Similar cases (Phonetic, Orthographic, Cross-Lingual)
- True Dissimilar cases (Unrelated domains, distinct anchors)
- Hard Negatives (Minimal vowel pairs, rhyming words, generic suffixes)

Calculates:
- Precision, Recall, F1-Score
- False Positives (over-blocking)
- False Negatives (under-blocking)
"""

import json
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import OVERALL_REJECTION_THRESHOLD
from backend.pipeline.stage1_preprocessor import extract_anchor_words
from backend.pipeline.stage4_integration import compare_title_against_candidate


def run_accuracy_evaluation(dataset_path: Path = BASE_DIR / "data" / "stage4_evaluation_dataset.json"):
    print("=" * 70)
    print("  PRGI Stage 4 Accuracy Evaluation")
    print("=" * 70)
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Loaded {len(data)} labeled evaluation pairs.\n")
    
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    
    details = []
    
    for idx, item in enumerate(data, 1):
        title_a = item["title_a"]
        title_b = item["title_b"]
        expected = item["expected_relation"].upper()
        reason = item["reason"]
        lang = item.get("language", "Unknown")
        
        # Extract anchor words
        s1_a = extract_anchor_words(title_a)
        s1_b = extract_anchor_words(title_b)
        
        clean_a = s1_a["cleaned_title"]
        clean_b = s1_b["cleaned_title"]
        anchor_a = s1_a["anchor_words"]
        anchor_b = s1_b["anchor_words"]
        
        res = compare_title_against_candidate(
            new_title=clean_a,
            candidate_title=clean_b,
            new_anchor=anchor_a,
            candidate_anchor=anchor_b
        )
        
        highest_sim = res["highest_similarity"]
        predicted = "SIMILAR" if highest_sim >= OVERALL_REJECTION_THRESHOLD else "DISSIMILAR"
        
        is_correct = (predicted == expected)
        
        if expected == "SIMILAR" and predicted == "SIMILAR":
            tp += 1
            status_tag = "[PASS] TRUE POSITIVE"
        elif expected == "DISSIMILAR" and predicted == "DISSIMILAR":
            tn += 1
            status_tag = "[PASS] TRUE NEGATIVE"
        elif expected == "DISSIMILAR" and predicted == "SIMILAR":
            fp += 1
            status_tag = "[FAIL] FALSE POSITIVE (Over-blocking)"
        else:
            fn += 1
            status_tag = "[FAIL] FALSE NEGATIVE (Under-blocking)"
            
        details.append({
            "idx": idx,
            "title_a": title_a,
            "title_b": title_b,
            "expected": expected,
            "predicted": predicted,
            "score": highest_sim,
            "ph_score": res["phonetic_similarity"],
            "ortho_score": res["orthographic_similarity"],
            "sem_score": res["semantic_similarity"],
            "is_correct": is_correct,
            "status_tag": status_tag,
            "reason": reason
        })
        
        print(f"[{idx:02d}] {status_tag} | Score: {highest_sim:.4f} (Ph:{res['phonetic_similarity']:.2f}, Or:{res['orthographic_similarity']:.2f}, Sem:{res['semantic_similarity']:.2f})")
        print(f"     '{title_a}' vs '{title_b}'")
        print(f"     Reason: {reason}\n")
        
    total = len(data)
    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    print("=" * 70)
    print("  EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Total Test Cases:       {total}")
    print(f"True Positives (TP):    {tp}")
    print(f"True Negatives (TN):    {tn}")
    print(f"False Positives (FP):   {fp}")
    print(f"False Negatives (FN):   {fn}")
    print(f"Accuracy:               {accuracy * 100:.2f}%")
    print(f"Precision:              {precision * 100:.2f}%")
    print(f"Recall:                 {recall * 100:.2f}%")
    print(f"F1-Score:               {f1 * 100:.2f}%")
    print("=" * 70)
    
    return {
        "total": total,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "details": details
    }


if __name__ == "__main__":
    run_accuracy_evaluation()
