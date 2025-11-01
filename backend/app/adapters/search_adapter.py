"""Web search adapter for evidence retrieval using Brave Search API."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import aiohttp
import re

logger = logging.getLogger(__name__)


class SearchAdapter:
    """Adapter for web search using Brave Search API."""

    def __init__(self, api_key: str = "", enable_real: bool = False):
        self.api_key = api_key
        self.enable_real = enable_real
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, queries: List[str], max_results: int = 10) -> Dict:
        """Search for evidence using Brave Search API."""
        if not self.enable_real or not self.api_key:
            return await self._mock_search(queries, max_results)
        
        return await self._real_search(queries, max_results)

    async def _real_search(self, queries: List[str], max_results: int) -> Dict:
        """Real Brave Search API call with improved sentiment analysis."""
        logger.info(f"[REAL] Searching Brave for {len(queries)} queries...")
        
        all_results = []
        claim_text = " ".join(queries).lower()
        
        try:
            async with aiohttp.ClientSession() as session:
                for query in queries[:3]:
                    headers = {
                        "Accept": "application/json",
                        "X-Subscription-Token": self.api_key
                    }
                    params = {
                        "q": query,
                        "count": 5
                    }
                    
                    async with session.get(self.base_url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = data.get("web", {}).get("results", [])
                            
                            for result in results[:5]:
                                all_results.append({
                                    "title": result.get("title", "Untitled"),
                                    "url": result.get("url", ""),
                                    "snippet": result.get("description", "")[:200],
                                    "published_at": datetime.utcnow(),
                                    "domain": result.get("url", "").split("/")[2] if result.get("url") else "",
                                    "score": 0.75,
                                    "sentiment": "neutral"
                                })
                        else:
                            logger.warning(f"[REAL] Brave API returned status {response.status}")
            
            if not all_results:
                logger.warning("[REAL] No results from Brave, falling back to mock")
                return await self._mock_search(queries, max_results)
            
            # IMPROVED: Context-aware sentiment analysis with negation detection
            supporting = 0
            refuting = 0
            
            for result in all_results:
                combined_text = (result["title"] + " " + result["snippet"]).lower()
                
                # CRITICAL: Check for negation patterns FIRST
                negation_patterns = [
                    r'\bno\s+(link|connection|evidence|relationship|association|correlation)\b',
                    r'\bdo\s+not\s+cause\b',
                    r'\bdoes\s+not\s+cause\b',
                    r'\bdoesn\'t\s+cause\b',
                    r'\bdidn\'t\s+cause\b',
                    r'\bnot\s+(linked|connected|associated|related)\b',
                    r'\bno\s+causal\b',
                    r'\bfound\s+no\b',
                    r'\bshows\s+no\b',
                ]
                
                has_negation = any(re.search(pattern, combined_text) for pattern in negation_patterns)
                
                # Strong refuting indicators (including negation)
                if has_negation or any(word in combined_text for word in [
                    "false", "debunked", "hoax", "fake", "myth", "conspiracy", 
                    "didn't happen", "never happened", "discredited", "retracted"
                ]):
                    result["sentiment"] = "refuting"
                    refuting += 1
                    logger.debug(f"[REAL] Marked as REFUTING (negation/false): {result['title'][:50]}")
                    continue
                
                # Strong supporting indicators (WITHOUT negation nearby)
                if any(word in combined_text for word in [
                    "confirmed", "verified", "proven", "documented", 
                    "evidence shows", "established fact", "research shows"
                ]):
                    result["sentiment"] = "supporting"
                    supporting += 1
                    logger.debug(f"[REAL] Marked as SUPPORTING: {result['title'][:50]}")
                    continue
                
                # SMART: Check if result provides factual details aligned with claim
                claim_keywords = self._extract_claim_keywords(claim_text)
                matches = sum(1 for keyword in claim_keywords if keyword in combined_text)
                
                # If many claim keywords + no negation = supporting
                if matches >= 2 and len(claim_keywords) > 0:
                    # Double-check for negative context
                    negative_context = any(neg in combined_text for neg in [
                        "not", "no", "never", "didn't", "doesn't", "isn't", "aren't", "wasn't", "weren't"
                    ])
                    
                    if not negative_context:
                        result["sentiment"] = "supporting"
                        supporting += 1
                        logger.debug(f"[REAL] Marked as SUPPORTING (keyword match, no negation): {matches}/{len(claim_keywords)} keywords")
                        continue
                
                # Default to neutral if unclear
                result["sentiment"] = "neutral"
            
            # Calculate score based on sentiment
            total = len(all_results)
            if total > 0:
                support_ratio = supporting / total
                refute_ratio = refuting / total
                
                if refute_ratio > 0.6:
                    score = 0.20  # Strongly refuting
                elif refute_ratio > 0.4:
                    score = 0.30  # Mostly refuting
                elif support_ratio > 0.6:
                    score = 0.85  # Strongly supporting
                elif support_ratio > 0.4:
                    score = 0.70  # Mostly supporting
                elif support_ratio > refute_ratio:
                    score = 0.60  # Slightly more support
                elif refute_ratio > support_ratio:
                    score = 0.40  # Slightly more refutation
                else:
                    score = 0.50  # Truly mixed/neutral
            else:
                score = 0.50
            
            logger.info(f"[REAL] Found {len(all_results)} results | Supporting: {supporting}, Refuting: {refuting}, Neutral: {total - supporting - refuting} | Score: {score}")
            
            return {
                "score": score,
                "sources": all_results[:10],
                "sources_found": len(all_results),
                "sources_supporting": supporting,
                "sources_refuting": refuting,
                "sources_neutral": total - supporting - refuting,
                "freshness_score": 0.88,
            }
            
        except Exception as e:
            logger.error(f"[REAL] Brave Search API error: {e}")
            return await self._mock_search(queries, max_results)

    def _extract_claim_keywords(self, claim: str) -> List[str]:
        """Extract key entities and facts from the claim for matching."""
        claim = claim.replace("did ", "").replace("is ", "").replace("are ", "")
        claim = claim.replace("was ", "").replace("were ", "").replace("will ", "")
        claim = claim.replace("?", "").strip()
        
        words = claim.split()
        keywords = []
        
        for i in range(len(words)):
            if words[i].istitle() or words[i].isdigit():
                keywords.append(words[i].lower())
            
            if i < len(words) - 1:
                phrase = f"{words[i]} {words[i+1]}".lower()
                keywords.append(phrase)
            
            if i < len(words) - 2:
                phrase = f"{words[i]} {words[i+1]} {words[i+2]}".lower()
                keywords.append(phrase)
        
        return keywords

    async def _mock_search(self, queries: List[str], max_results: int) -> Dict:
        """Mock search for testing."""
        logger.info(f"[MOCK] Searching for {len(queries)} queries...")
        
        query_text = " ".join(queries).lower()
        
        false_keywords = ["earth is flat", "moon is made of cheese", "vaccines cause autism"]
        true_keywords = ["water is wet", "sky is blue", "earth revolves around sun"]
        
        is_false = any(keyword in query_text for keyword in false_keywords)
        is_true = any(keyword in query_text for keyword in true_keywords)
        
        mock_results = []
        
        if is_false:
            sentiments = ["refuting", "refuting", "refuting", "supporting"]
        elif is_true:
            sentiments = ["supporting", "supporting", "supporting", "refuting"]
        else:
            sentiments = ["supporting", "refuting", "supporting", "refuting"]
        
        for i, query in enumerate(queries[:2]):
            for j in range(2):
                idx = i * 2 + j
                sentiment = sentiments[min(idx, len(sentiments) - 1)]
                
                mock_results.append({
                    "title": f"Source {idx + 1}: {query[:40]}",
                    "url": f"https://example-source-{idx + 1}.com/article",
                    "snippet": f"According to experts, the claim appears {'substantiated' if sentiment == 'supporting' else 'disputed'}.",
                    "published_at": datetime.utcnow() - timedelta(days=i),
                    "domain": f"source{idx + 1}.com",
                    "score": 0.85 - (i * 0.1),
                    "sentiment": sentiment,
                })
        
        supporting = sum(1 for r in mock_results if r["sentiment"] == "supporting")
        refuting = sum(1 for r in mock_results if r["sentiment"] == "refuting")
        
        if refuting > supporting:
            score = 0.20
        elif supporting > refuting:
            score = 0.85
        else:
            score = 0.55
        
        return {
            "score": score,
            "sources": mock_results[:5],
            "sources_found": len(mock_results),
            "sources_supporting": supporting,
            "sources_refuting": refuting,
            "sources_neutral": 0,
            "freshness_score": 0.88,
        }

    async def close(self):
        """Close adapter resources."""
        pass
