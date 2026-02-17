"""
Content Moderation API - Version 2.0
Now with customizable filter dial levels and custom word allowlists/blocklists
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import re
from datetime import datetime
from collections import defaultdict
from time import time

app = FastAPI(
    title="Content Moderation API",
    description="AI-powered text moderation with customizable filter dial levels",
    version="2.0.0"
)

# ─────────────────────────────────────────────
# RATE LIMITING
# ─────────────────────────────────────────────
# Simple in-memory rate limiter (100 requests per minute per IP)
rate_limit_store = defaultdict(list)
RATE_LIMIT = 100  # requests per minute
RATE_WINDOW = 60  # seconds

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limit requests to 100 per minute per IP address"""
    # Skip rate limiting for root and health endpoints
    if request.url.path in ["/", "/health", "/dial-info", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    client_ip = request.client.host
    current_time = time()
    
    # Clean old requests outside the time window
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if current_time - req_time < RATE_WINDOW
    ]
    
    # Check if rate limit exceeded
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Maximum {RATE_LIMIT} requests per minute. Please try again later or get an API key at RapidAPI.",
                "retry_after": 60
            }
        )
    
    # Add current request
    rate_limit_store[client_ip].append(current_time)
    
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(RATE_LIMIT - len(rate_limit_store[client_ip]))
    response.headers["X-RateLimit-Reset"] = str(int(current_time + RATE_WINDOW))
    
    return response

# ─────────────────────────────────────────────
# FILTER DIAL LEVELS (1-5)
# ─────────────────────────────────────────────
# Level 1 - Family Safe     : Block everything (kids apps, schools)
# Level 2 - Teen Friendly   : Allow mild language, block slurs/hate
# Level 3 - General         : Allow cursing, block hate speech/slurs
# Level 4 - Mature          : Allow most language, block only slurs/threats
# Level 5 - Minimal         : Only block hate speech and threats

DIAL_CONFIGS = {
    1: {
        "name": "Family Safe",
        "description": "Strictest filtering. Blocks all profanity, toxicity, spam, hate speech.",
        "emoji": "👨‍👩‍👧‍👦",
        "best_for": "Kids apps, schools, family platforms",
        "block_categories": ["profanity", "toxicity", "hate_speech", "spam"],
        "sensitivity_multiplier": 1.5
    },
    2: {
        "name": "Teen Friendly",
        "description": "Allows mild language but blocks strong profanity, hate speech, spam.",
        "emoji": "🎮",
        "best_for": "Teen gaming, student platforms, youth communities",
        "block_categories": ["hate_speech", "spam", "toxicity"],
        "allowed_words": ["damn", "hell", "crap"],  # mild words allowed
        "sensitivity_multiplier": 1.0
    },
    3: {
        "name": "General",
        "description": "Allows cursing between adults. Blocks hate speech, slurs, threats, spam.",
        "emoji": "💬",
        "best_for": "General chat apps, gaming, forums, Discord servers",
        "block_categories": ["hate_speech", "spam"],
        "allowed_words": ["damn", "hell", "crap", "shit", "fuck", "ass", "bitch"],
        "sensitivity_multiplier": 1.0
    },
    4: {
        "name": "Mature",
        "description": "Allows most adult language. Only blocks slurs, threats, and spam.",
        "emoji": "🔞",
        "best_for": "Adult communities, 18+ platforms, mature gaming",
        "block_categories": ["hate_speech", "spam"],
        "sensitivity_multiplier": 0.7
    },
    5: {
        "name": "Minimal",
        "description": "Lightest filtering. Only blocks hate speech and direct threats.",
        "emoji": "🔓",
        "best_for": "Open forums, debate platforms, free speech communities",
        "block_categories": ["hate_speech"],
        "sensitivity_multiplier": 0.5
    }
}

# ─────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────

class ModerationRequest(BaseModel):
    text: str = Field(..., description="Text content to moderate", max_length=10000)
    dial: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Filter dial level 1-5. 1=Family Safe, 3=General, 5=Minimal"
    )
    custom_blocked_words: Optional[List[str]] = Field(
        default=None,
        description="Extra words to always block regardless of dial level"
    )
    custom_allowed_words: Optional[List[str]] = Field(
        default=None,
        description="Words to always allow regardless of dial level"
    )

class CategoryScore(BaseModel):
    category: str
    detected: bool
    confidence: float
    severity: str

class ModerationResponse(BaseModel):
    flagged: bool
    overall_score: float
    dial_level: int
    dial_name: str
    categories: List[CategoryScore]
    filtered_text: Optional[str] = None
    timestamp: str
    processing_time_ms: float


# ─────────────────────────────────────────────
# CORE MODERATION ENGINE
# ─────────────────────────────────────────────

class ContentModerator:
    def __init__(self):
        # Pattern libraries per category
        self.patterns = {
            "profanity": [
                r'\b(fuck|shit|damn|ass|bitch|bastard|crap)\b',
                r'\b(hell|piss|dick|cock|pussy)\b',
            ],
            "toxicity": [
                r'\b(idiot|stupid|dumb|moron|retard)\b',
                r'\b(hate|kill|die|death)\s+(you|yourself)',
                r'(shut\s+up|fuck\s+off)',
            ],
            "hate_speech": [
                r'\b(racist|sexist|homophobic|transphobic)\b',
                r'\b(n[i1]gg[ae]r|f[a4]gg[o0]t)\b',
            ],
            "spam": [
                r'(click here|buy now|limited time|act now).*(http|www)',
                r'(viagra|cialis|pharmacy|pills).*\$',
                r'(earn \$|make money|work from home).*guaranteed',
            ]
        }

    def _build_effective_patterns(
        self,
        category: str,
        dial_config: dict,
        custom_blocked: List[str],
        custom_allowed: List[str]
    ) -> List[str]:
        """Build the effective pattern list based on dial + custom words"""
        patterns = list(self.patterns.get(category, []))

        # Add custom blocked words as patterns
        if custom_blocked:
            for word in custom_blocked:
                patterns.append(rf'\b({re.escape(word)})\b')

        # Remove patterns that match allowed words
        if custom_allowed or dial_config.get("allowed_words"):
            all_allowed = set(custom_allowed or [])
            all_allowed.update(dial_config.get("allowed_words", []))

            filtered_patterns = []
            for p in patterns:
                # Keep pattern only if it doesn't solely match allowed words
                skip = False
                for word in all_allowed:
                    # If the pattern is a simple word match, check if it's allowed
                    simple_match = re.fullmatch(
                        r'\\b\(([^)]+)\)\\b', p.replace('\\b', r'\b')
                    )
                    if word.lower() in p.lower() and re.search(
                        rf'\b{re.escape(word)}\b', word, re.IGNORECASE
                    ):
                        skip = True
                        break
                if not skip:
                    filtered_patterns.append(p)
            return filtered_patterns

        return patterns

    def detect_category(
        self,
        text: str,
        patterns: List[str],
        multiplier: float
    ) -> Dict:
        """Score text against a set of patterns"""
        text_lower = text.lower()
        matches = 0

        for pattern in patterns:
            try:
                matches += len(re.findall(pattern, text_lower, re.IGNORECASE))
            except re.error:
                continue

        text_length = max(len(text.split()), 1)
        base_score = min(matches / text_length * 10, 1.0)
        confidence = min(base_score * multiplier, 1.0)
        detected = confidence > 0.3

        if confidence < 0.3:
            severity = "low"
        elif confidence < 0.6:
            severity = "medium"
        else:
            severity = "high"

        return {
            "detected": detected,
            "confidence": round(confidence, 3),
            "severity": severity
        }

    def moderate(
        self,
        text: str,
        dial: int = 3,
        custom_blocked_words: Optional[List[str]] = None,
        custom_allowed_words: Optional[List[str]] = None
    ) -> Dict:
        """Main moderation function with dial support"""
        start_time = datetime.now()

        dial_config = DIAL_CONFIGS[dial]
        categories_to_check = dial_config["block_categories"]
        multiplier = dial_config["sensitivity_multiplier"]

        custom_blocked = custom_blocked_words or []
        custom_allowed = custom_allowed_words or []

        category_scores = []
        total_confidence = 0

        for category in categories_to_check:
            effective_patterns = self._build_effective_patterns(
                category, dial_config, custom_blocked, custom_allowed
            )
            result = self.detect_category(text, effective_patterns, multiplier)
            category_scores.append({
                "category": category,
                "detected": result["detected"],
                "confidence": result["confidence"],
                "severity": result["severity"]
            })
            total_confidence += result["confidence"]

        # Also check custom blocked words across all content
        if custom_blocked:
            custom_patterns = [rf'\b({re.escape(w)})\b' for w in custom_blocked]
            custom_result = self.detect_category(text, custom_patterns, 1.5)
            if custom_result["detected"]:
                category_scores.append({
                    "category": "custom_blocked",
                    "detected": True,
                    "confidence": custom_result["confidence"],
                    "severity": custom_result["severity"]
                })
                total_confidence += custom_result["confidence"]

        n = len(category_scores) or 1
        overall_score = total_confidence / n
        flagged = any(cat["detected"] for cat in category_scores)

        filtered_text = self._filter_text(
            text, dial_config, custom_blocked, custom_allowed
        ) if flagged else None

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "flagged": flagged,
            "overall_score": round(overall_score, 3),
            "dial_level": dial,
            "dial_name": dial_config["name"],
            "categories": category_scores,
            "filtered_text": filtered_text,
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": round(processing_time, 2)
        }

    def _filter_text(
        self,
        text: str,
        dial_config: dict,
        custom_blocked: List[str],
        custom_allowed: List[str]
    ) -> str:
        """Replace flagged content with asterisks"""
        filtered = text
        categories_to_block = dial_config["block_categories"]

        for category in categories_to_block:
            for pattern in self.patterns.get(category, []):
                # Don't filter if word is in allowed list
                allowed = set(custom_allowed or [])
                allowed.update(dial_config.get("allowed_words", []))
                try:
                    filtered = re.sub(
                        pattern,
                        lambda m: m.group() if any(
                            a.lower() in m.group().lower() for a in allowed
                        ) else '*' * len(m.group()),
                        filtered,
                        flags=re.IGNORECASE
                    )
                except re.error:
                    continue

        # Always filter custom blocked words
        for word in custom_blocked:
            try:
                filtered = re.sub(
                    rf'\b{re.escape(word)}\b',
                    '*' * len(word),
                    filtered,
                    flags=re.IGNORECASE
                )
            except re.error:
                continue

        return filtered


# ─────────────────────────────────────────────
# INITIALIZE + ENDPOINTS
# ─────────────────────────────────────────────

moderator = ContentModerator()

@app.get("/")
async def root():
    return {
        "service": "Content Moderation API",
        "version": "2.0.0",
        "status": "active",
        "new_in_v2": "Customizable filter dial (levels 1-5) + custom word lists",
        "endpoints": {
            "moderate": "/moderate",
            "dial_info": "/dial-info",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/dial-info")
async def dial_info():
    """Get information about all dial levels"""
    return {
        "description": "Filter dial levels control how strictly content is moderated",
        "levels": DIAL_CONFIGS
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/moderate", response_model=ModerationResponse)
async def moderate_content(request: ModerationRequest):
    """
    Moderate text with customizable dial level

    - **text**: Text to analyze (required)
    - **dial**: Filter level 1-5 (default: 3 = General)
      - 1 = Family Safe (block everything)
      - 2 = Teen Friendly (allow mild language)
      - 3 = General (allow cursing, block hate/spam)
      - 4 = Mature (allow most language, block slurs/threats)
      - 5 = Minimal (only block hate speech)
    - **custom_blocked_words**: Extra words to always block
    - **custom_allowed_words**: Words to always allow
    """
    try:
        result = moderator.moderate(
            text=request.text,
            dial=request.dial,
            custom_blocked_words=request.custom_blocked_words,
            custom_allowed_words=request.custom_allowed_words
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Moderation failed: {str(e)}")

@app.post("/batch-moderate")
async def batch_moderate(texts: List[str], dial: int = 3):
    """Moderate multiple texts with the same dial level"""
    if len(texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts per batch")
    results = []
    for text in texts:
        try:
            results.append(moderator.moderate(text=text, dial=dial))
        except Exception as e:
            results.append({"error": str(e)})
    return {"total": len(texts), "dial": dial, "results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
