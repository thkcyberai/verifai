"""Facti.ai adapter for media forensics."""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class StubFactiAIAdapter:
    """Stub adapter for demo without real API calls."""

    async def analyze_media(self, media_url: str, media_type: str) -> Dict:
        """Return mock forensics results."""
        logger.info(f"[STUB] Analyzing {media_type} at {media_url[:50]}...")
        
        manipulation_detected = False
        deepfake_prob = 0.08
        integrity = 0.92
        anomalies = []
        
        if "fake" in media_url.lower() or "manipulated" in media_url.lower():
            manipulation_detected = True
            deepfake_prob = 0.76
            integrity = 0.31
            anomalies = [
                {
                    "type": "audio_splice",
                    "confidence": 0.87,
                    "description": "Audio waveform discontinuity detected",
                },
                {
                    "type": "metadata_inconsistency",
                    "confidence": 0.92,
                    "description": "File creation date inconsistent with claimed date",
                },
            ]
        
        manipulation_score = 1.0 - integrity if manipulation_detected else 0.1
        authenticity_score = (integrity + (1.0 - manipulation_score)) / 2
        
        return {
            "score": round(authenticity_score, 2),
            "manipulation_detected": manipulation_detected,
            "anomalies": anomalies,
            "deepfake_probability": deepfake_prob,
            "integrity_score": integrity,
        }

    async def close(self):
        pass
