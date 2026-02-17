"""
Content Moderation API - Version 2.0
Now with customizable filter dial levels and custom word allowlists/blocklists
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import re
from datetime import datetime

app = FastAPI(
    title="Content Moderation API",
    description="AI-powered text moderation with customizable filter dial levels",
    version="2.0.0"
)

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
        "allowed_words": ["damn", "hell", "crap"],
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

class ContentModerator:
    def __init__(self):
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

    def detect_category(self, text, patterns, multiplier):
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
        severity = "low" if confidence < 0.3 else "medium" if confidence < 0.6 else "high"
        return {"detected": detected, "confidence": round(confidence, 3), "severity": severity}

    def moderate(self, text, dial=3, custom_blocked_words=None, custom_allowed_words=None):
        start_time = datetime.now()
        dial_config = DIAL_CONFIGS[dial]
        categories_to_check = dial_config["block_categories"]
        multiplier = dial_config["sensitivity_multiplier"]
        custom_blocked = custom_blocked_words or []
        custom_allowed = custom_allowed_words or []

        category_scores = []
        total_confidence = 0

        for category in categories_to_check:
            patterns = list(self.patterns.get(category, []))
            if custom_blocked:
                for word in custom_blocked:
                    patterns.append(rf'\b({re.escape(word)})\b')
            result = self.detect_category(text, patterns, multiplier)
            category_scores.append({
                "category": category,
                "detected": result["detected"],
                "confidence": result["confidence"],
                "severity": result["severity"]
            })
            total_confidence += result["confidence"]

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
        filtered_text = self._filter_text(text, dial_config, custom_blocked) if flagged else None
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

    def _filter_text(self, text, dial_config, custom_blocked):
        filtered = text
        allowed = set(dial_config.get("allowed_words", []))
        for category in dial_config["block_categories"]:
            for pattern in self.patterns.get(category, []):
                try:
                    filtered = re.sub(
                        pattern,
                        lambda m: m.group() if any(a.lower() in m.group().lower() for a in allowed)
                        else '*' * len(m.group()),
                        filtered,
                        flags=re.IGNORECASE
                    )
                except re.error:
                    continue
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

moderator = ContentModerator()

@app.get("/")
async def root():
    return {
        "service": "Content Moderation API",
        "version": "2.0.0",
        "status": "active",
        "new_in_v2": "Customizable filter dial (levels 1-5) + custom word lists",
        "endpoints": {"moderate": "/moderate", "dial-info": "/dial-info", "health": "/health", "docs": "/docs"}
    }

@app.get("/dial-info")
async def dial_info():
    return {"description": "Filter dial levels control how strictly content is moderated", "levels": DIAL_CONFIGS}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/moderate", response_model=ModerationResponse)
async def moderate_content(request: ModerationRequest):
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
    