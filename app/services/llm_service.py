"""Gemini LLM integration service for candidate evaluation.

Features:
- Structured prompt construction
- Retry logic with exponential backoff (up to 3 attempts)
- Robust JSON response parsing (handles markdown fences, raw text)
- Graceful error handling with fallback responses
"""

import json
import re
import time
import logging
import google.generativeai as genai
from typing import Dict
from app.config import GEMINI_API_KEY
from app.prompts.screening import SCREENING_PROMPT

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds


def evaluate_candidate(candidate_data: Dict, role_config: Dict) -> Dict:
    """
    Evaluate a candidate's pitch against role criteria using Gemini LLM.
    
    Implements retry logic with exponential backoff for transient failures.
    
    Returns:
        Dict with keys: score, reasoning, eligibility, skills_assessment, pitch_assessment
    """
    # Build the prompt
    prompt = SCREENING_PROMPT.format(
        role_title=role_config["title"],
        required_skills=", ".join(role_config["required_skills"]),
        min_experience_years=role_config["min_experience_years"],
        location_constraints=", ".join(role_config["location_constraints"]),
        evaluation_criteria=role_config["evaluation_criteria"],
        candidate_name=candidate_data["name"],
        candidate_skills=", ".join(candidate_data["skills"]),
        candidate_experience=candidate_data["years_experience"],
        candidate_location=candidate_data["location"],
        candidate_pitch=candidate_data["pitch"],
    )

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "LLM evaluation attempt %d/%d for candidate '%s' (role: %s)",
                attempt, MAX_RETRIES, candidate_data["name"], role_config["role_id"]
            )

            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            
            # Parse JSON response from LLM
            result = _parse_llm_response(response.text)
            
            logger.info(
                "LLM evaluation succeeded: score=%d, eligibility=%s (attempt %d)",
                result["score"], result["eligibility"], attempt
            )
            return result
            
        except Exception as e:
            last_error = e
            logger.warning(
                "LLM evaluation attempt %d failed: %s", attempt, str(e)
            )
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                logger.info("Retrying in %.1f seconds...", delay)
                time.sleep(delay)

    # All retries exhausted
    logger.error(
        "LLM evaluation failed after %d attempts for candidate '%s'. Last error: %s",
        MAX_RETRIES, candidate_data["name"], str(last_error)
    )
    return {
        "score": 0,
        "reasoning": f"LLM evaluation failed after {MAX_RETRIES} attempts: {str(last_error)}",
        "eligibility": "Ineligible",
        "skills_assessment": "Could not assess due to LLM error",
        "pitch_assessment": "Could not assess due to LLM error",
    }


def _parse_llm_response(text: str) -> Dict:
    """Parse the LLM response text into a structured dict.
    
    Handles multiple response formats:
    1. Clean JSON
    2. JSON wrapped in markdown code fences
    3. JSON embedded in natural language text
    """
    text = text.strip()
    
    # Remove markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        text = text.strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                result = json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.error("Failed to parse extracted JSON from LLM response")
                return {
                    "score": 0,
                    "reasoning": f"Failed to parse LLM response as JSON. Raw: {text[:500]}",
                    "eligibility": "Ineligible",
                    "skills_assessment": "Parse error",
                    "pitch_assessment": "Parse error",
                }
        else:
            logger.error("No JSON found in LLM response")
            return {
                "score": 0,
                "reasoning": f"No JSON found in LLM response. Raw: {text[:500]}",
                "eligibility": "Ineligible",
                "skills_assessment": "Parse error",
                "pitch_assessment": "Parse error",
            }

    # Validate and sanitize
    score = max(0, min(100, int(result.get("score", 0))))
    eligibility = result.get("eligibility", "Ineligible")
    if eligibility not in ("Eligible", "Ineligible"):
        eligibility = "Eligible" if score >= 50 else "Ineligible"

    return {
        "score": score,
        "reasoning": result.get("reasoning", "No reasoning provided"),
        "eligibility": eligibility,
        "skills_assessment": result.get("skills_assessment", ""),
        "pitch_assessment": result.get("pitch_assessment", ""),
    }
