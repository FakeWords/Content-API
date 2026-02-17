"""
Test script for Content Moderation API
Run this to see the API in action with example texts
"""

import requests
import json
from typing import Dict

# API endpoint (when running locally)
BASE_URL = "http://localhost:8000"

def test_api(text: str, sensitivity: str = "medium", categories: list = None):
    """Test the moderation API with sample text"""
    
    payload = {
        "text": text,
        "sensitivity": sensitivity
    }
    
    if categories:
        payload["categories"] = categories
    
    try:
        response = requests.post(f"{BASE_URL}/moderate", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "API is not running. Start it first with: python content_moderation_api.py"}
    except Exception as e:
        return {"error": str(e)}

def print_result(test_name: str, result: Dict):
    """Pretty print test results"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"🚩 Flagged: {result['flagged']}")
    print(f"📊 Overall Score: {result['overall_score']}")
    print(f"⏱️  Processing Time: {result['processing_time_ms']}ms")
    
    print(f"\n📋 Categories:")
    for cat in result['categories']:
        emoji = "🔴" if cat['detected'] else "🟢"
        print(f"  {emoji} {cat['category'].upper()}: {cat['confidence']} ({cat['severity']} severity)")
    
    if result.get('filtered_text'):
        print(f"\n🔒 Filtered Text:")
        print(f"  {result['filtered_text']}")

# Test cases
if __name__ == "__main__":
    print("🧪 Content Moderation API Test Suite")
    print("=" * 60)
    
    # Test 1: Clean text
    result1 = test_api("Hello! This is a perfectly normal and friendly message.")
    print_result("Clean Text", result1)
    
    # Test 2: Profanity
    result2 = test_api("This is some bullshit and you're a damn fool.")
    print_result("Profanity Detection", result2)
    
    # Test 3: Toxic content
    result3 = test_api("You're so stupid and dumb. Just shut up already.")
    print_result("Toxicity Detection", result3)
    
    # Test 4: Spam
    result4 = test_api("CLICK HERE NOW! Buy viagra cheap! Limited time offer! www.scam.com")
    print_result("Spam Detection", result4)
    
    # Test 5: High sensitivity
    result5 = test_api("That's kind of stupid.", sensitivity="high")
    print_result("High Sensitivity Mode", result5)
    
    # Test 6: Specific categories only
    result6 = test_api("Damn, this is bullshit spam!", categories=["profanity"])
    print_result("Profanity Only Check", result6)
    
    # Test 7: Batch moderation
    print(f"\n{'='*60}")
    print("TEST: Batch Moderation")
    print(f"{'='*60}")
    
    batch_texts = [
        "Hello world",
        "This is damn annoying",
        "You're an idiot"
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/batch-moderate",
            params={"sensitivity": "medium"},
            json=batch_texts
        )
        batch_result = response.json()
        print(f"✅ Processed {batch_result['total']} texts")
        for i, result in enumerate(batch_result['results'], 1):
            print(f"\n  Text {i}: Flagged={result.get('flagged', 'N/A')}, Score={result.get('overall_score', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Test suite complete!")
    print("💡 Try the interactive docs at: http://localhost:8000/docs")
    print(f"{'='*60}\n")
