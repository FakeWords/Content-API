"""
Content Moderation API - MVP Version
A simple API that analyzes text for toxicity, profanity, and inappropriate content
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import re
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="Content Moderation API",
    description="AI-powered text moderation for detecting toxicity, profanity, and inappropriate content",
    version="1.0.0"
)

# Request/Response Models
class ModerationRequest(BaseModel):
    text: str = Field(..., description="Text content to moderate", max_length=10000)
    sensitivity: str = Field(default="medium", description="Sensitivity level: low, medium, high")
    categories: Optional[List[str]] = Field(
        default=None, 
        description="Specific categories to check: toxicity, profanity, spam, hate_speech"
    )

class CategoryScore(BaseModel):
    category: str
    detected: bool
    confidence: float
    severity: str  # low, medium, high

class ModerationResponse(BaseModel):
    flagged: bool
    overall_score: float
    categories: List[CategoryScore]
    filtered_text: Optional[str] = None
    timestamp: str
    processing_time_ms: float

# Simple pattern-based detection (MVP - we'll enhance this later)
class ContentModerator:
    def __init__(self):
        # Profanity patterns (basic set for demo)
        self.profanity_patterns = [
            r'\b(fuck|shit|damn|ass|bitch|bastard|crap)\b',
            r'\b(hell|piss|dick|cock|pussy)\b',
        ]
        
        # Toxicity patterns
        self.toxicity_patterns = [
            r'\b(idiot|stupid|dumb|moron|retard)\b',
            r'\b(hate|kill|die|death)\s+(you|yourself)',
            r'(shut\s+up|fuck\s+off)',
        ]
        
        # Hate speech patterns (basic)
        self.hate_speech_patterns = [
            r'\b(racist|sexist|homophobic|transphobic)\b',
            r'\b(n[i1]gg[ae]r|f[a4]gg[o0]t)\b',
        ]
        
        # Spam patterns
        self.spam_patterns = [
            r'(click here|buy now|limited time|act now).*(http|www)',
            r'(viagra|cialis|pharmacy|pills).*\$',
            r'(earn \$|make money|work from home).*guaranteed',
        ]
        
        self.sensitivity_multipliers = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.5
        }
    
    def detect_category(self, text: str, patterns: List[str], sensitivity: str) -> Dict:
        """Detect if text matches patterns for a category"""
        text_lower = text.lower()
        matches = 0
        
        for pattern in patterns:
            matches += len(re.findall(pattern, text_lower, re.IGNORECASE))
        
        # Calculate confidence based on matches and text length
        text_length = max(len(text.split()), 1)
        base_score = min(matches / text_length * 10, 1.0)
        
        # Apply sensitivity multiplier
        multiplier = self.sensitivity_multipliers[sensitivity]
        confidence = min(base_score * multiplier, 1.0)
        
        detected = confidence > 0.3
        
        # Determine severity
        if confidence < 0.3:
            severity = "low"
        elif confidence < 0.6:
            severity = "medium"
        else:
            severity = "high"
        
        return {
            "detected": detected,
            "confidence": round(confidence, 3),
            "severity": severity,
            "match_count": matches
        }
    
    def moderate(self, text: str, sensitivity: str = "medium", 
                 categories: Optional[List[str]] = None) -> Dict:
        """Main moderation function"""
        start_time = datetime.now()
        
        # Default to all categories if none specified
        if not categories:
            categories = ["profanity", "toxicity", "hate_speech", "spam"]
        
        results = {}
        category_map = {
            "profanity": self.profanity_patterns,
            "toxicity": self.toxicity_patterns,
            "hate_speech": self.hate_speech_patterns,
            "spam": self.spam_patterns
        }
        
        category_scores = []
        total_confidence = 0
        
        for category in categories:
            if category in category_map:
                result = self.detect_category(text, category_map[category], sensitivity)
                category_scores.append({
                    "category": category,
                    "detected": result["detected"],
                    "confidence": result["confidence"],
                    "severity": result["severity"]
                })
                total_confidence += result["confidence"]
        
        # Calculate overall score
        overall_score = total_confidence / len(categories) if categories else 0
        flagged = any(cat["detected"] for cat in category_scores)
        
        # Generate filtered text if flagged
        filtered_text = None
        if flagged:
            filtered_text = self._filter_text(text)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "flagged": flagged,
            "overall_score": round(overall_score, 3),
            "categories": category_scores,
            "filtered_text": filtered_text,
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": round(processing_time, 2)
        }
    
    def _filter_text(self, text: str) -> str:
        """Replace inappropriate content with asterisks"""
        filtered = text
        all_patterns = (
            self.profanity_patterns + 
            self.toxicity_patterns + 
            self.hate_speech_patterns
        )
        
        for pattern in all_patterns:
            filtered = re.sub(pattern, lambda m: '*' * len(m.group()), filtered, flags=re.IGNORECASE)
        
        return filtered

# Initialize moderator
moderator = ContentModerator()

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Content Moderation API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "moderate": "/moderate",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/moderate", response_model=ModerationResponse)
async def moderate_content(request: ModerationRequest):
    """
    Moderate text content for inappropriate material
    
    - **text**: The text content to analyze (required, max 10000 chars)
    - **sensitivity**: Detection sensitivity (low/medium/high, default: medium)
    - **categories**: Specific categories to check (optional)
    
    Returns detailed moderation results including confidence scores and filtered text
    """
    try:
        result = moderator.moderate(
            text=request.text,
            sensitivity=request.sensitivity,
            categories=request.categories
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Moderation failed: {str(e)}")

@app.post("/batch-moderate")
async def batch_moderate(texts: List[str], sensitivity: str = "medium"):
    """
    Moderate multiple texts in a single request
    
    - **texts**: List of text strings to moderate
    - **sensitivity**: Detection sensitivity for all texts
    
    Returns list of moderation results
    """
    if len(texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts per batch request")
    
    results = []
    for text in texts:
        try:
            result = moderator.moderate(text=text, sensitivity=sensitivity)
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "text": text[:50] + "..."})
    
    return {
        "total": len(texts),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
