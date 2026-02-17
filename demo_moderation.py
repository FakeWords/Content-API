"""
Content Moderation Demo (No Dependencies Required)
This demonstrates the core moderation logic without needing to run a web server
"""

import re
from datetime import datetime
from typing import List, Dict, Optional

class ContentModerator:
    """
    Core moderation engine - this is the brain of your API
    """
    
    def __init__(self):
        # Pattern libraries for different categories
        # These are simple regex patterns that match problematic content
        
        # Profanity patterns (basic set for demo)
        self.profanity_patterns = [
            r'\b(fuck|shit|damn|ass|bitch|bastard|crap)\b',
            r'\b(hell|piss|dick|cock|pussy)\b',
        ]
        
        # Toxicity patterns (insults, attacks)
        self.toxicity_patterns = [
            r'\b(idiot|stupid|dumb|moron|retard)\b',
            r'\b(hate|kill|die|death)\s+(you|yourself)',
            r'(shut\s+up|fuck\s+off)',
        ]
        
        # Hate speech patterns
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
        
        # Sensitivity multipliers affect how strict detection is
        self.sensitivity_multipliers = {
            'low': 0.5,      # Less strict - fewer false positives
            'medium': 1.0,   # Balanced
            'high': 1.5      # More strict - catches borderline content
        }
    
    def detect_category(self, text: str, patterns: List[str], sensitivity: str) -> Dict:
        """
        Check if text matches patterns for a specific category
        
        Returns:
        - detected: bool (is problematic content found?)
        - confidence: float 0-1 (how sure are we?)
        - severity: string (low/medium/high)
        - match_count: int (how many patterns matched?)
        """
        text_lower = text.lower()
        matches = 0
        
        # Count how many patterns match in the text
        for pattern in patterns:
            matches += len(re.findall(pattern, text_lower, re.IGNORECASE))
        
        # Calculate confidence score
        # More matches = higher confidence
        # Shorter text with matches = higher confidence
        text_length = max(len(text.split()), 1)
        base_score = min(matches / text_length * 10, 1.0)
        
        # Apply sensitivity multiplier
        multiplier = self.sensitivity_multipliers[sensitivity]
        confidence = min(base_score * multiplier, 1.0)
        
        # Threshold: 0.3+ = detected
        detected = confidence > 0.3
        
        # Determine severity level
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
        """
        Main moderation function - analyzes text across all categories
        
        Args:
            text: The text to analyze
            sensitivity: 'low', 'medium', or 'high'
            categories: Optional list of specific categories to check
        
        Returns:
            Complete moderation report with scores and filtered text
        """
        start_time = datetime.now()
        
        # Default to checking all categories
        if not categories:
            categories = ["profanity", "toxicity", "hate_speech", "spam"]
        
        # Map category names to their pattern lists
        category_map = {
            "profanity": self.profanity_patterns,
            "toxicity": self.toxicity_patterns,
            "hate_speech": self.hate_speech_patterns,
            "spam": self.spam_patterns
        }
        
        category_scores = []
        total_confidence = 0
        
        # Check each category
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
        
        # Calculate overall score (average of all categories)
        overall_score = total_confidence / len(categories) if categories else 0
        
        # Flagged = at least one category detected something
        flagged = any(cat["detected"] for cat in category_scores)
        
        # Generate filtered/cleaned version if problematic
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
        """
        Replace problematic content with asterisks
        Example: "This is shit" → "This is ****"
        """
        filtered = text
        all_patterns = (
            self.profanity_patterns + 
            self.toxicity_patterns + 
            self.hate_speech_patterns
        )
        
        for pattern in all_patterns:
            # Replace matched text with asterisks of same length
            filtered = re.sub(
                pattern, 
                lambda m: '*' * len(m.group()), 
                filtered, 
                flags=re.IGNORECASE
            )
        
        return filtered


def print_result(test_name: str, result: Dict):
    """Pretty print moderation results"""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")
    print(f"🚩 Flagged: {result['flagged']}")
    print(f"📊 Overall Score: {result['overall_score']}")
    print(f"⏱️  Processing Time: {result['processing_time_ms']}ms")
    
    print(f"\n📋 Category Results:")
    for cat in result['categories']:
        emoji = "🔴" if cat['detected'] else "🟢"
        print(f"  {emoji} {cat['category'].upper():<15} "
              f"Confidence: {cat['confidence']:<5} "
              f"({cat['severity']} severity)")
    
    if result.get('filtered_text'):
        print(f"\n🔒 Filtered Version:")
        print(f"  {result['filtered_text']}")
    
    print()


if __name__ == "__main__":
    # Initialize the moderator
    moderator = ContentModerator()
    
    print("🧪 CONTENT MODERATION ENGINE - DEMO")
    print("=" * 70)
    print("This demonstrates the core logic that powers your API")
    print("=" * 70)
    
    # Test Case 1: Clean content
    result1 = moderator.moderate(
        "Hello! This is a perfectly normal and friendly message. Have a great day!"
    )
    print_result("Clean Text (Should Pass)", result1)
    
    # Test Case 2: Profanity
    result2 = moderator.moderate(
        "This is some bullshit and you're a damn fool."
    )
    print_result("Profanity Detection", result2)
    
    # Test Case 3: Toxicity
    result3 = moderator.moderate(
        "You're so stupid and dumb. Just shut up already, moron."
    )
    print_result("Toxic Language", result3)
    
    # Test Case 4: Spam
    result4 = moderator.moderate(
        "CLICK HERE NOW! Buy viagra cheap! Limited time offer guaranteed! www.scam.com Make money from home!"
    )
    print_result("Spam Detection", result4)
    
    # Test Case 5: Mixed issues
    result5 = moderator.moderate(
        "This shit is so stupid. You're an idiot."
    )
    print_result("Multiple Violations", result5)
    
    # Test Case 6: High sensitivity (catches borderline content)
    result6 = moderator.moderate(
        "That's kind of stupid.", 
        sensitivity="high"
    )
    print_result("High Sensitivity Mode", result6)
    
    # Test Case 7: Low sensitivity (more lenient)
    result7 = moderator.moderate(
        "That's kind of stupid.", 
        sensitivity="low"
    )
    print_result("Low Sensitivity Mode (Same Text)", result7)
    
    # Test Case 8: Specific category check only
    result8 = moderator.moderate(
        "Damn, this is bullshit spam! Click here now!",
        categories=["profanity"]  # Only check profanity, ignore spam
    )
    print_result("Profanity Check Only (Ignoring Spam)", result8)
    
    print("=" * 70)
    print("✅ DEMO COMPLETE!")
    print("=" * 70)
    print("\n💡 Key Takeaways:")
    print("  • Processing time: ~1-5ms (extremely fast!)")
    print("  • Customizable sensitivity levels")
    print("  • Multiple categories can be checked")
    print("  • Automatic text filtering available")
    print("  • Ready to wrap in an API and deploy")
    print("\n📚 Next Steps:")
    print("  1. Wrap this in FastAPI (see content_moderation_api.py)")
    print("  2. Deploy to cloud (Railway, Heroku, AWS)")
    print("  3. List on API marketplace (RapidAPI, DigitalAPI)")
    print("  4. Start getting customers!")
    print()
