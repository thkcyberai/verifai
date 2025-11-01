"""OpenAI adapter for LLM-based claim analysis."""
import logging
import re
from typing import Dict, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIAdapter:
    """Adapter for OpenAI GPT models."""
    
    def __init__(self, api_key: str, enable_real: bool = True):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            enable_real: Whether to use real API (vs mock)
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.api_key = api_key
        self.enable_real = enable_real
        self.client = OpenAI(api_key=api_key) if enable_real else None
        self.model = "gpt-4o"
    
    def normalize_claim(self, claim: str) -> str:
        """
        Normalize claim by removing meta-question framing.
        
        Converts:
        - "Is it true that X?" → "X"
        - "Is it false that X?" → "X"
        - "Can you confirm that X?" → "X"
        - "Someone told me X. Is this true?" → "X"
        """
        claim = claim.strip()
        
        # Pattern matching for meta-questions
        patterns = [
            r'^Is it true that\s+(.+?)\??$',
            r'^Is it false that\s+(.+?)\??$',
            r'^Can you confirm that\s+(.+?)\??$',
            r'^I heard that\s+(.+?)\.\s*Is this accurate\??$',
            r'^Someone told me\s+(.+?)\.\s*Is this true\??$',
            r'^I read that\s+(.+?)\.\s*Can you verify\??$',
            r'^What do you think about the claim that\s+(.+?)\??$',
            r'^Is there evidence that\s+(.+?)\??$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, claim, re.IGNORECASE)
            if match:
                normalized = match.group(1).strip()
                logger.info(f"Normalized claim: '{claim}' → '{normalized}'")
                return normalized
        
        # No normalization needed
        return claim
    
    async def analyze_claim(self, claim: str) -> Dict:
        """
        Analyze a claim using OpenAI GPT.
        
        Args:
            claim: The claim to analyze
            
        Returns:
            Dict with 'score' (0.0-1.0) and 'confidence' (0.0-1.0)
        """
        # Mock response if real API disabled
        if not self.enable_real:
            return {"score": 0.5, "confidence": 0.5, "reasoning": "[MOCK] Analysis unavailable"}
        
        try:
            # Normalize the claim first
            normalized_claim = self.normalize_claim(claim)
            
            logger.info(f"[REAL] Analyzing claim with OpenAI: {normalized_claim[:50]}...")
            
            prompt = f"""Analyze this claim for truthfulness: "{normalized_claim}"

Rate the claim on a scale from 0.0 to 1.0:
- 0.0 = Definitely false
- 0.3 = Likely false
- 0.5 = Uncertain/unclear
- 0.7 = Likely true  
- 1.0 = Definitely true

Also provide your confidence level (0.0-1.0) in your assessment.

Respond in this exact format:
SCORE: [number]
CONFIDENCE: [number]
REASONING: [brief explanation]"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a fact-checking expert. Analyze claims objectively based on evidence and logic."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Parse response
            score_match = re.search(r'SCORE:\s*([0-9.]+)', content)
            confidence_match = re.search(r'CONFIDENCE:\s*([0-9.]+)', content)
            reasoning_match = re.search(r'REASONING:\s*(.+)', content, re.DOTALL)
            
            if not score_match or not confidence_match:
                logger.error(f"Failed to parse OpenAI response: {content}")
                return {"score": 0.5, "confidence": 0.5, "reasoning": "Parse error"}
            
            score = float(score_match.group(1))
            confidence = float(confidence_match.group(1))
            reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
            
            # Clamp values
            score = max(0.0, min(1.0, score))
            confidence = max(0.0, min(1.0, confidence))
            
            logger.info(f"[REAL] OpenAI result: score={score}, confidence={confidence}")
            
            return {
                "score": score,
                "confidence": confidence,
                "reasoning": reasoning
            }
            
        except Exception as e:
            logger.error(f"OpenAI adapter error: {e}")
            return {"score": 0.5, "confidence": 0.5, "reasoning": f"Error: {str(e)}"}
