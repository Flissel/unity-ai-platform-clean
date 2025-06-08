#!/usr/bin/env python3
"""
Example ML inference script for UnityAI Python Worker.
"""

import json
import sys
from typing import Dict, Any, List, Union
import re


def sentiment_analysis(text: str) -> Dict[str, Any]:
    """Simple rule-based sentiment analysis."""
    
    # Simple sentiment lexicon
    positive_words = {
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
        'awesome', 'brilliant', 'outstanding', 'superb', 'love', 'like',
        'happy', 'pleased', 'satisfied', 'perfect', 'best', 'incredible'
    }
    
    negative_words = {
        'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate', 
        'dislike', 'angry', 'frustrated', 'disappointed', 'worst', 'pathetic',
        'useless', 'broken', 'failed', 'poor', 'sad', 'upset'
    }
    
    # Clean and tokenize text
    words = re.findall(r'\b\w+\b', text.lower())
    
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    
    total_sentiment_words = positive_count + negative_count
    
    if total_sentiment_words == 0:
        sentiment = "neutral"
        confidence = 0.5
    elif positive_count > negative_count:
        sentiment = "positive"
        confidence = min(0.9, 0.5 + (positive_count - negative_count) / len(words))
    elif negative_count > positive_count:
        sentiment = "negative"
        confidence = min(0.9, 0.5 + (negative_count - positive_count) / len(words))
    else:
        sentiment = "neutral"
        confidence = 0.5
    
    return {
        "sentiment": sentiment,
        "confidence": round(confidence, 3),
        "positive_words_found": positive_count,
        "negative_words_found": negative_count,
        "total_words": len(words)
    }


def text_classification(text: str, categories: List[str] = None) -> Dict[str, Any]:
    """Simple keyword-based text classification."""
    
    if not categories:
        categories = ['technology', 'business', 'sports', 'entertainment', 'politics']
    
    # Simple keyword mapping
    category_keywords = {
        'technology': ['computer', 'software', 'ai', 'machine learning', 'programming', 'code', 'tech', 'digital', 'internet', 'app'],
        'business': ['company', 'market', 'profit', 'revenue', 'investment', 'finance', 'economy', 'corporate', 'startup', 'entrepreneur'],
        'sports': ['game', 'team', 'player', 'score', 'match', 'championship', 'league', 'tournament', 'athlete', 'coach'],
        'entertainment': ['movie', 'music', 'celebrity', 'film', 'show', 'actor', 'singer', 'concert', 'album', 'entertainment'],
        'politics': ['government', 'election', 'president', 'policy', 'vote', 'political', 'congress', 'senate', 'democracy', 'campaign']
    }
    
    text_lower = text.lower()
    scores = {}
    
    for category in categories:
        if category in category_keywords:
            keywords = category_keywords[category]
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[category] = score
        else:
            scores[category] = 0
    
    # Normalize scores
    total_score = sum(scores.values())
    if total_score > 0:
        probabilities = {cat: score / total_score for cat, score in scores.items()}
        predicted_category = max(probabilities, key=probabilities.get)
        confidence = probabilities[predicted_category]
    else:
        probabilities = {cat: 1.0 / len(categories) for cat in categories}
        predicted_category = "unknown"
        confidence = 0.0
    
    return {
        "predicted_category": predicted_category,
        "confidence": round(confidence, 3),
        "probabilities": {cat: round(prob, 3) for cat, prob in probabilities.items()},
        "keyword_matches": scores
    }


def extract_entities(text: str) -> Dict[str, Any]:
    """Simple named entity extraction using regex patterns."""
    
    entities = {
        "emails": re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text),
        "urls": re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text),
        "phone_numbers": re.findall(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b', text),
        "dates": re.findall(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b', text, re.IGNORECASE),
        "numbers": re.findall(r'\b\d+(?:\.\d+)?\b', text),
        "capitalized_words": re.findall(r'\b[A-Z][a-z]+\b', text)
    }
    
    # Clean up phone numbers
    entities["phone_numbers"] = [f"({match[0]}) {match[1]}-{match[2]}" for match in entities["phone_numbers"]]
    
    return {
        "entities": entities,
        "entity_counts": {key: len(value) for key, value in entities.items()}
    }


def run_inference(model_type: str, input_data: Union[str, List[str]], **kwargs) -> Dict[str, Any]:
    """Run ML inference based on model type."""
    
    try:
        if model_type == "sentiment":
            if isinstance(input_data, list):
                results = [sentiment_analysis(text) for text in input_data]
                return {"model_type": model_type, "results": results}
            else:
                return {"model_type": model_type, "result": sentiment_analysis(input_data)}
        
        elif model_type == "classification":
            categories = kwargs.get("categories")
            if isinstance(input_data, list):
                results = [text_classification(text, categories) for text in input_data]
                return {"model_type": model_type, "results": results}
            else:
                return {"model_type": model_type, "result": text_classification(input_data, categories)}
        
        elif model_type == "entity_extraction":
            if isinstance(input_data, list):
                results = [extract_entities(text) for text in input_data]
                return {"model_type": model_type, "results": results}
            else:
                return {"model_type": model_type, "result": extract_entities(input_data)}
        
        else:
            return {"error": f"Unknown model type: {model_type}"}
    
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python ml_inference.py <model_type> <input_text> [categories]"}))
        sys.exit(1)
    
    try:
        model_type = sys.argv[1]
        input_data = sys.argv[2]
        
        kwargs = {}
        if len(sys.argv) > 3 and model_type == "classification":
            kwargs["categories"] = sys.argv[3].split(",")
        
        result = run_inference(model_type, input_data, **kwargs)
        print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()