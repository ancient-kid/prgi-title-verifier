"""
Stage 3: The 'Frankentitle' (Combination Check) Engine

Identifies if a submitted title is a combination/concatenation of two or more existing registered titles
(e.g., "Hindu Indian Express" formed from "The Hindu" and "The Indian Express").

Uses set membership partitioning across registered title and anchor sets.
"""

from typing import Any, Dict, List, Optional, Set, Tuple


class FrankentitleDetector:
    def __init__(self, registered_titles: Optional[Set[str]] = None, anchor_set: Optional[Set[str]] = None):
        """
        Initialize with registered title sets.
        """
        self.registered_titles: Set[str] = set()
        self.anchor_set: Set[str] = set()
        
        if registered_titles:
            self.load_titles(registered_titles, anchor_set)

    def load_titles(self, titles: Set[str], anchor_set: Optional[Set[str]] = None):
        """Load normalized titles and anchors."""
        self.registered_titles = {t.lower().strip() for t in titles if t and len(t.strip()) > 2}
        if anchor_set:
            self.anchor_set = {a.lower().strip() for a in anchor_set if a and len(a.strip()) > 2}
        else:
            self.anchor_set = self.registered_titles

    def check_combination(self, cleaned_title: str, tokens: List[str]) -> Dict[str, Any]:
        """
        Check if the cleaned title is formed by concatenating two or more registered titles / anchors.
        """
        if len(tokens) < 2 or not self.registered_titles:
            return {
                "is_frankentitle": False,
                "components": [],
                "explanation": "Title length insufficient for compound title check or title index empty.",
                "probability_multiplier": 1.0
            }
            
        n = len(tokens)
        
        # Check 2-way splits: tokens[0:i] and tokens[i:n]
        for i in range(1, n):
            part1 = " ".join(tokens[:i]).strip()
            part2 = " ".join(tokens[i:]).strip()
            
            # Check if part1 and part2 are in registered titles or significant anchor sets
            p1_match = (part1 in self.registered_titles) or (part1 in self.anchor_set)
            p2_match = (part2 in self.registered_titles) or (part2 in self.anchor_set)
            
            if p1_match and p2_match:
                return {
                    "is_frankentitle": True,
                    "components": [part1.title(), part2.title()],
                    "explanation": (
                        f"Frankentitle Combination Violation (Stage 3): Submitted title '{cleaned_title.title()}' "
                        f"is an unauthorized combination of two registered titles/anchors: '{part1.title()}' and '{part2.title()}'."
                    ),
                    "probability_multiplier": 0.0
                }
                
        # Check 3-way splits if tokens >= 3
        if n >= 3:
            for i in range(1, n - 1):
                for j in range(i + 1, n):
                    p1 = " ".join(tokens[:i]).strip()
                    p2 = " ".join(tokens[i:j]).strip()
                    p3 = " ".join(tokens[j:]).strip()
                    
                    if (p1 in self.registered_titles or p1 in self.anchor_set) and \
                       (p2 in self.registered_titles or p2 in self.anchor_set) and \
                       (p3 in self.registered_titles or p3 in self.anchor_set):
                        return {
                            "is_frankentitle": True,
                            "components": [p1.title(), p2.title(), p3.title()],
                            "explanation": (
                                f"Frankentitle Combination Violation (Stage 3): Submitted title is a combination of three "
                                f"registered titles: '{p1.title()}', '{p2.title()}', and '{p3.title()}'."
                            ),
                            "probability_multiplier": 0.0
                        }

        return {
            "is_frankentitle": False,
            "components": [],
            "explanation": "Passed Frankentitle combination check. No unauthorized compound title detected.",
            "probability_multiplier": 1.0
        }
