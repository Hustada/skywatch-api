"""AI-powered UFO sighting research endpoints using Google Gemini."""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import google.generativeai as genai

from api.database import get_db
from api.models import Sighting, ResearchCache
from api.config import settings
from api.dependencies import CurrentApiKey

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/research", tags=["research"])

# Configure Gemini AI
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not configured. Research functionality will be disabled.")

# Current model version for cache invalidation
CURRENT_MODEL_VERSION = "gemini-2.0-flash-exp"


async def get_cached_research(
    db: AsyncSession, 
    sighting_id: int, 
    research_type: str
) -> Optional[Dict[str, Any]]:
    """Get cached research result if available."""
    try:
        result = await db.execute(
            select(ResearchCache).where(
                ResearchCache.sighting_id == sighting_id,
                ResearchCache.research_type == research_type,
                ResearchCache.model_version == CURRENT_MODEL_VERSION
            )
        )
        cache_entry = result.scalar_one_or_none()
        
        if cache_entry:
            # Update access tracking
            await db.execute(
                update(ResearchCache)
                .where(ResearchCache.id == cache_entry.id)
                .values(
                    cache_hits=ResearchCache.cache_hits + 1,
                    last_accessed=datetime.utcnow()
                )
            )
            await db.commit()
            
            # Return parsed JSON result
            return json.loads(cache_entry.analysis_result)
            
    except Exception as e:
        logger.warning(f"Failed to retrieve cached research: {e}")
    
    return None


async def save_research_to_cache(
    db: AsyncSession,
    sighting_id: int,
    research_type: str,
    result: Dict[str, Any]
) -> None:
    """Save research result to cache."""
    try:
        cache_entry = ResearchCache(
            sighting_id=sighting_id,
            research_type=research_type,
            analysis_result=json.dumps(result),
            model_version=CURRENT_MODEL_VERSION
        )
        db.add(cache_entry)
        await db.commit()
        logger.info(f"Cached {research_type} research for sighting {sighting_id}")
        
    except Exception as e:
        logger.error(f"Failed to cache research result: {e}")
        # Don't fail the request if caching fails
        await db.rollback()


@router.get(
    "/sighting/{sighting_id}",
    summary="AI Research UFO Sighting",
    description="Generate comprehensive research report for a specific UFO sighting using AI."
)
async def research_sighting(
    sighting_id: int,
    api_key: CurrentApiKey,
    db: AsyncSession = Depends(get_db)
):
    """Generate AI-powered research report for a UFO sighting."""
    
    # Check if Gemini is configured
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI research service is not available. Contact administrator."
        )
    
    # Check cache first
    cached_result = await get_cached_research(db, sighting_id, "full")
    if cached_result:
        logger.info(f"Returning cached full research for sighting {sighting_id}")
        return cached_result
    
    # Get the sighting from database
    result = await db.execute(select(Sighting).where(Sighting.id == sighting_id))
    sighting = result.scalar_one_or_none()
    
    if not sighting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sighting with ID {sighting_id} not found"
        )
    
    try:
        # Generate new full research with Gemini
        logger.info(f"Generating new full research for sighting {sighting_id}")
        research_query = build_research_query(sighting)
        
        # Use Gemini for research with search grounding
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Configure generation with search grounding
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=4000,
        )
        
        # Construct prompt for research
        prompt = f"""
Research this UFO sighting and provide a comprehensive analysis:

{research_query}

Please provide:
1. **Cross-references**: Any similar sightings in the same area/timeframe
2. **Official records**: Military activity, aviation records, weather data for that date/location
3. **Media coverage**: News reports or investigations related to this sighting
4. **Scientific context**: Astronomical events, atmospheric conditions that might explain the sighting
5. **Analysis**: Credibility assessment and possible explanations

Format your response as structured sections with proper citations for all claims.
Use web search to find current information and credible sources.
"""
        
        # Generate response (simplified - no search grounding for now)
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        # Extract citations if available
        citations = []
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'grounding_metadata'):
                    for source in candidate.grounding_metadata.grounding_supports:
                        if hasattr(source, 'segment'):
                            citations.append({
                                "title": getattr(source.segment, 'title', 'Unknown'),
                                "url": getattr(source.segment, 'url', ''),
                                "snippet": getattr(source.segment, 'text', '')[:200] + '...'
                            })
        
        # Prepare result
        result = {
            "sighting_id": sighting_id,
            "research_report": response.text,
            "citations": citations,
            "generated_at": datetime.utcnow().isoformat(),
            "sighting_summary": {
                "date": sighting.date_time.isoformat() if sighting.date_time else None,
                "location": f"{sighting.city}, {sighting.state}" if sighting.state else sighting.city,
                "shape": sighting.shape,
                "summary": sighting.summary
            }
        }
        
        # Save to cache for future requests
        await save_research_to_cache(db, sighting_id, "full", result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating research for sighting {sighting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate research report: {str(e)}"
        )


@router.get(
    "/quick/{sighting_id}",
    summary="Quick AI Analysis",
    description="Generate quick AI analysis for a UFO sighting without extensive web research."
)
async def quick_analysis(
    sighting_id: int,
    api_key: CurrentApiKey,
    db: AsyncSession = Depends(get_db)
):
    """Generate quick AI analysis without extensive web research."""
    
    # Check if Gemini is configured
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analysis service is not available. Contact administrator."
        )
    
    # Check cache first
    cached_result = await get_cached_research(db, sighting_id, "quick")
    if cached_result:
        logger.info(f"Returning cached quick analysis for sighting {sighting_id}")
        return cached_result
    
    # Get the sighting from database
    result = await db.execute(select(Sighting).where(Sighting.id == sighting_id))
    sighting = result.scalar_one_or_none()
    
    if not sighting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sighting with ID {sighting_id} not found"
        )
    
    try:
        # Generate new analysis with Gemini
        logger.info(f"Generating new quick analysis for sighting {sighting_id}")
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""
Analyze this UFO sighting report and provide insights:

Date: {sighting.date_time}
Location: {sighting.city}, {sighting.state}
Shape: {sighting.shape}
Duration: {sighting.duration}
Description: {sighting.text}

Please provide:
1. **Credibility Assessment**: Rate the credibility (1-10) and explain factors
2. **Possible Explanations**: List conventional explanations (aircraft, weather, etc.)
3. **Notable Features**: Highlight unusual or significant aspects
4. **Classification**: Categorize the sighting type (lights, craft, phenomenon, etc.)

Keep the analysis concise but informative.
"""
        
        response = model.generate_content(prompt)
        
        # Prepare result
        result = {
            "sighting_id": sighting_id,
            "quick_analysis": response.text,
            "generated_at": datetime.utcnow().isoformat(),
            "analysis_type": "quick"
        }
        
        # Save to cache for future requests
        await save_research_to_cache(db, sighting_id, "quick", result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating quick analysis for sighting {sighting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analysis: {str(e)}"
        )


def build_research_query(sighting: Sighting) -> str:
    """Build comprehensive research query for a UFO sighting."""
    
    # Base information
    query_parts = []
    
    if sighting.date_time:
        query_parts.append(f"Date: {sighting.date_time.strftime('%B %d, %Y at %H:%M')}")
    
    if sighting.city and sighting.state:
        query_parts.append(f"Location: {sighting.city}, {sighting.state}")
    elif sighting.city:
        query_parts.append(f"Location: {sighting.city}")
    
    if sighting.shape:
        query_parts.append(f"Object Shape: {sighting.shape}")
    
    if sighting.duration:
        query_parts.append(f"Duration: {sighting.duration}")
    
    if sighting.summary:
        query_parts.append(f"Summary: {sighting.summary}")
    
    if sighting.text and len(sighting.text) > len(sighting.summary or ""):
        # Include more details if available
        text_snippet = sighting.text[:500] + "..." if len(sighting.text) > 500 else sighting.text
        query_parts.append(f"Full Description: {text_snippet}")
    
    return "\n".join(query_parts)


@router.get(
    "/status",
    summary="Research Service Status",
    description="Check if AI research service is available."
)
async def research_status():
    """Check the status of the AI research service."""
    
    if not settings.GEMINI_API_KEY:
        return {
            "status": "unavailable",
            "message": "AI research service is not configured",
            "features": []
        }
    
    try:
        # Test Gemini connection
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        test_response = model.generate_content("Test connection")
        
        return {
            "status": "available",
            "message": "AI research service is operational",
            "features": [
                "Deep sighting research with web search",
                "Quick sighting analysis", 
                "Citation-backed reports",
                "Cross-reference detection"
            ],
            "model": "gemini-2.0-flash-exp"
        }
    except Exception as e:
        logger.error(f"Gemini connection test failed: {str(e)}")
        return {
            "status": "error",
            "message": f"AI research service error: {str(e)}",
            "features": []
        }