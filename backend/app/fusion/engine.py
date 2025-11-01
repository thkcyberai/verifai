"""Fusion engine for combining multiple verification signals."""
import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Decision(str, Enum):
    """Verification decision."""
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNVERIFIED = "UNVERIFIED"


class FusionEngine:
    """Combines signals from multiple adapters into a final verdict."""
    
    # Fusion weights (must sum to 1.0)
    WEIGHTS = {
        'media_forensics': 0.45,
        'evidence': 0.35,
        'llm_reasoning': 0.20
    }
    
    # Decision thresholds
    FALSE_THRESHOLD = 0.40  # UPDATED from 0.30 to 0.40
    TRUE_THRESHOLD = 0.70   # Unchanged
    
    def __init__(self):
        """Initialize fusion engine."""
        self.rules_triggered = []
    
    def fuse(
        self,
        media_score: Optional[float],
        evidence_score: Optional[float],
        llm_score: Optional[float],
        llm_confidence: Optional[float] = None
    ) -> Tuple[Decision, float, float]:
        """
        Fuse multiple verification signals into a final decision.
        
        Args:
            media_score: Media forensics score (0.0-1.0)
            evidence_score: Evidence verification score (0.0-1.0)
            llm_score: LLM reasoning score (0.0-1.0)
            llm_confidence: LLM confidence level (0.0-1.0)
            
        Returns:
            Tuple of (Decision, confidence, raw_score)
        """
        self.rules_triggered = []
        
        # High-confidence LLM override (when LLM is very confident)
        if llm_confidence and llm_confidence >= 0.90 and llm_score is not None:
            if llm_score >= 0.70:
                self.rules_triggered.append("high_confidence_llm_true")
                return Decision.TRUE, min(0.95, llm_confidence), llm_score
            elif llm_score <= 0.30:
                self.rules_triggered.append("high_confidence_llm_false")
                return Decision.FALSE, min(0.95, llm_confidence), llm_score
        
        # Calculate weighted average of available scores
        total_weight = 0.0
        weighted_sum = 0.0
        
        if media_score is not None:
            weighted_sum += media_score * self.WEIGHTS['media_forensics']
            total_weight += self.WEIGHTS['media_forensics']
        
        if evidence_score is not None:
            weighted_sum += evidence_score * self.WEIGHTS['evidence']
            total_weight += self.WEIGHTS['evidence']
        
        if llm_score is not None:
            weighted_sum += llm_score * self.WEIGHTS['llm_reasoning']
            total_weight += self.WEIGHTS['llm_reasoning']
        
        # Normalize if not all scores available
        if total_weight == 0:
            logger.warning("No scores available for fusion")
            self.rules_triggered.append("no_scores_available")
            return Decision.UNVERIFIED, 0.5, 0.5
        
        raw_score = weighted_sum / total_weight
        
        # Apply decision thresholds
        if raw_score <= self.FALSE_THRESHOLD:
            self.rules_triggered.append("below_false_threshold")
            confidence = self._calculate_confidence(raw_score, Decision.FALSE)
            return Decision.FALSE, confidence, raw_score
        
        elif raw_score >= self.TRUE_THRESHOLD:
            self.rules_triggered.append("above_true_threshold")
            confidence = self._calculate_confidence(raw_score, Decision.TRUE)
            return Decision.TRUE, confidence, raw_score
        
        else:
            # Middle zone - inconclusive
            self.rules_triggered.append("inconclusive_middle_range")
            # Lower confidence when in the uncertain zone
            confidence = 0.5 - abs(raw_score - 0.5) * 0.2
            return Decision.UNVERIFIED, confidence, raw_score
    
    def _calculate_confidence(self, raw_score: float, decision: Decision) -> float:
        """
        Calculate confidence level based on how far the score is from thresholds.
        
        Args:
            raw_score: The raw fusion score
            decision: The decision made
            
        Returns:
            Confidence level (0.0-1.0)
        """
        if decision == Decision.FALSE:
            # More confident when score is closer to 0.0
            distance_from_zero = raw_score
            confidence = max(0.9, 1.0 - (distance_from_zero / self.FALSE_THRESHOLD))
            return min(0.95, confidence)
        
        elif decision == Decision.TRUE:
            # More confident when score is closer to 1.0
            distance_from_one = 1.0 - raw_score
            confidence = max(0.9, 1.0 - (distance_from_one / (1.0 - self.TRUE_THRESHOLD)))
            return min(0.95, confidence)
        
        else:
            # UNVERIFIED has lower confidence
            return 0.5
    
    def get_fusion_details(self) -> Dict:
        """Get details about the fusion decision."""
        return {
            "weights": self.WEIGHTS,
            "thresholds": {
                "false": self.FALSE_THRESHOLD,
                "true": self.TRUE_THRESHOLD
            },
            "rules_triggered": self.rules_triggered
        }


# Compatibility wrapper for existing code
def fuse_scores(
    llm_score: Optional[float],
    evidence_score: Optional[float],
    media_score: Optional[float],
    llm_confidence: Optional[float]
) -> Tuple[Decision, float, Dict]:
    """
    Wrapper function for backward compatibility.
    
    Args:
        llm_score: LLM reasoning score
        evidence_score: Evidence verification score  
        media_score: Media forensics score
        llm_confidence: LLM confidence level
    
    Returns:
        Tuple of (Decision, confidence, fusion_details_dict)
    """
    engine = FusionEngine()
    decision, confidence, raw_score = engine.fuse(
        media_score=media_score,
        evidence_score=evidence_score,
        llm_score=llm_score,
        llm_confidence=llm_confidence
    )
    
    fusion_details = engine.get_fusion_details()
    fusion_details['raw_score'] = raw_score
    
    return decision, confidence, fusion_details
