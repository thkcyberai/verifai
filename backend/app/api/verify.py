"""Verify endpoint for claim verification."""
import asyncio
import logging
import time
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from app.adapters import get_factiai_adapter, get_openai_adapter, get_search_adapter
from app.fusion.engine import fuse_scores
from app.models.schemas import (
    CheckScores,
    Evidence,
    Source,
    VerifyRequest,
    VerifyResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/verify", response_model=VerifyResponse)
async def verify_claim(request: Request, verify_request: VerifyRequest):
    """Verify a claim or media."""
    request_id = getattr(request.state, "request_id", "unknown")
    claim_id = f"clm_{uuid4().hex[:12]}"
    start_time = time.time()

    logger.info(f"Verify request: claim_id={claim_id} | has_claim={bool(verify_request.claim)}")

    try:
        if not verify_request.claim and not verify_request.media_url:
            raise ValueError("Either claim or media_url must be provided")

        # Initialize adapters
        openai_adapter = get_openai_adapter()
        search_adapter = get_search_adapter()
        factiai_adapter = get_factiai_adapter()

        # Run checks in parallel
        claim_text = verify_request.claim or "Verify authenticity"

        tasks = {
            "llm": asyncio.create_task(openai_adapter.analyze_claim(claim_text)),
            "evidence": asyncio.create_task(search_adapter.search([claim_text])),
        }

        if verify_request.media_url:
            tasks["media"] = asyncio.create_task(
                factiai_adapter.analyze_media(verify_request.media_url, "video")
            )

        # Wait for results
        results = {}
        for key, task in tasks.items():
            try:
                results[key] = await task
            except Exception as e:
                logger.error(f"{key} check failed: {e}")
                results[key] = None

        # Extract scores
        llm_result = results.get("llm")
        evidence_result = results.get("evidence")
        media_result = results.get("media")

        llm_score = llm_result["score"] if llm_result else None
        evidence_score = evidence_result["score"] if evidence_result else None
        media_score = media_result["score"] if media_result else None

        # Fuse scores
        decision, confidence, fusion_details = fuse_scores(llm_score, evidence_score, media_score, llm_result.get("confidence"))

        # Map decision to verdict
        # Use decision value directly (already in correct format)
        verdict = decision.value

        # Generate reasoning
        reasoning_parts = []
        if llm_result:
            reasoning_parts.append(llm_result.get("reasoning", ""))
        if evidence_result:
            supporting = evidence_result.get("sources_supporting", 0)
            refuting = evidence_result.get("sources_refuting", 0)
            if refuting > supporting:
                reasoning_parts.append("Multiple sources refute this claim.")
            elif supporting > refuting:
                reasoning_parts.append("Multiple sources support this claim.")

        reasoning = " ".join(reasoning_parts) or f"Analysis suggests this claim is {verdict.lower()}."

        # Convert citations to Evidence and Sources
        evidence_list = []
        sources_list = []
        
        if evidence_result:
            for idx, source in enumerate(evidence_result.get("sources", [])[:5]):
                # Add to evidence
                evidence_list.append(
                    Evidence(
                        source=source.get("title", "Unknown Source"),
                        title=source.get("title", "Untitled"),
                        snippet=source.get("snippet", "No description available.")[:200],
                        url=source.get("url", ""),
                        relevance_score=source.get("score", 0.5),
                    )
                )
                # Add to sources
                sources_list.append(
                    Source(
                        url=source.get("url", ""),
                        title=source.get("title", "Untitled"),
                        credibility=source.get("score", 0.5),
                    )
                )

        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Verification complete: {verdict} | confidence={confidence} | {latency_ms}ms")

        return VerifyResponse(
            id=claim_id,
            claim=claim_text,
            verdict=verdict,
            confidence=confidence,
            reasoning=reasoning,
            evidence=evidence_list,
            sources=sources_list,
            media_analysis=None,
            created_at=datetime.utcnow(),
            request_id=request_id,
            checks=CheckScores(
                llm_reasoning_score=llm_score,
                evidence_score=evidence_score,
                media_forensics_score=media_score,
            ),
            partial=False,
            latency_ms=latency_ms,
        )

    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await search_adapter.close()
        await factiai_adapter.close()
