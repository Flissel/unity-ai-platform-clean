#!/usr/bin/env python3
"""
Text Analysis and ML Inference Script for n8n Integration

This script performs various text analysis and machine learning inference tasks
and can be executed directly from n8n workflows using the Execute Command node.

Usage:
  python3 text_analysis.py --input '{"text": "Hello world", "task": "sentiment"}'
  python3 text_analysis.py --input-file input.json --task classification
"""

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Suppress warnings
warnings.filterwarnings('ignore')

# Add shared libs to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'libs'))
from common import (
    handle_errors, setup_logging, validate_input, safe_json_loads,
    create_success_response, create_error_response, measure_execution_time
)
from config import get_config

# Setup logging
logger = setup_logging()
config = get_config()


@measure_execution_time
@handle_errors
def analyze_text(
    text: Union[str, List[str]],
    task: str = "sentiment",
    model_name: Optional[str] = None,
    language: str = "en",
    batch_size: int = 32
) -> Dict[str, Any]:
    """Perform text analysis using various ML models."""
    
    logger.info(f"Starting text analysis with task: {task}")
    
    # Convert single text to list for uniform processing
    texts = [text] if isinstance(text, str) else text
    
    if task == "sentiment":
        return analyze_sentiment(texts, model_name, language)
    elif task == "classification":
        return classify_text(texts, model_name, language)
    elif task == "ner":
        return extract_entities(texts, model_name, language)
    elif task == "summarization":
        return summarize_text(texts, model_name, language)
    elif task == "translation":
        return translate_text(texts, model_name, language)
    elif task == "keywords":
        return extract_keywords(texts, model_name, language)
    elif task == "similarity":
        return calculate_similarity(texts, model_name, language)
    elif task == "language_detection":
        return detect_language(texts)
    elif task == "readability":
        return analyze_readability(texts, language)
    elif task == "toxicity":
        return detect_toxicity(texts, model_name)
    else:
        return create_error_response(
            f"Unknown task: {task}",
            "ValueError",
            {"available_tasks": [
                "sentiment", "classification", "ner", "summarization", 
                "translation", "keywords", "similarity", "language_detection",
                "readability", "toxicity"
            ]}
        )


def analyze_sentiment(texts: List[str], model_name: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
    """Analyze sentiment of texts."""
    
    try:
        # Try transformers first
        try:
            from transformers import pipeline
            
            model = model_name or "cardiffnlp/twitter-roberta-base-sentiment-latest"
            classifier = pipeline("sentiment-analysis", model=model, return_all_scores=True)
            
            results = []
            for text in texts:
                scores = classifier(text[:512])[0]  # Limit text length
                
                # Normalize scores
                sentiment_map = {
                    "NEGATIVE": "negative",
                    "NEUTRAL": "neutral", 
                    "POSITIVE": "positive",
                    "LABEL_0": "negative",
                    "LABEL_1": "neutral",
                    "LABEL_2": "positive"
                }
                
                normalized_scores = {}
                for score in scores:
                    label = sentiment_map.get(score["label"], score["label"].lower())
                    normalized_scores[label] = score["score"]
                
                # Determine overall sentiment
                overall_sentiment = max(normalized_scores, key=normalized_scores.get)
                confidence = normalized_scores[overall_sentiment]
                
                results.append({
                    "text": text,
                    "sentiment": overall_sentiment,
                    "confidence": round(confidence, 4),
                    "scores": normalized_scores
                })
            
            return create_success_response({
                "results": results,
                "model_used": model,
                "task": "sentiment"
            }, {
                "texts_processed": len(texts),
                "average_confidence": round(sum(r["confidence"] for r in results) / len(results), 4)
            })
        
        except ImportError:
            # Fallback to TextBlob
            try:
                from textblob import TextBlob
                
                results = []
                for text in texts:
                    blob = TextBlob(text)
                    polarity = blob.sentiment.polarity
                    
                    if polarity > 0.1:
                        sentiment = "positive"
                    elif polarity < -0.1:
                        sentiment = "negative"
                    else:
                        sentiment = "neutral"
                    
                    confidence = abs(polarity)
                    
                    results.append({
                        "text": text,
                        "sentiment": sentiment,
                        "confidence": round(confidence, 4),
                        "polarity": round(polarity, 4),
                        "subjectivity": round(blob.sentiment.subjectivity, 4)
                    })
                
                return create_success_response({
                    "results": results,
                    "model_used": "TextBlob",
                    "task": "sentiment"
                }, {
                    "texts_processed": len(texts),
                    "average_confidence": round(sum(r["confidence"] for r in results) / len(results), 4)
                })
            
            except ImportError:
                return create_error_response(
                    "No sentiment analysis libraries available. Install transformers or textblob.",
                    "ImportError",
                    {"required_packages": ["transformers", "torch", "textblob"]}
                )
    
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return create_error_response(
            f"Sentiment analysis failed: {str(e)}",
            type(e).__name__
        )


def classify_text(texts: List[str], model_name: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
    """Classify texts into categories."""
    
    try:
        from transformers import pipeline
        
        model = model_name or "facebook/bart-large-mnli"
        classifier = pipeline("zero-shot-classification", model=model)
        
        # Default categories
        candidate_labels = [
            "business", "technology", "politics", "sports", "entertainment",
            "health", "science", "education", "travel", "food", "lifestyle"
        ]
        
        results = []
        for text in texts:
            result = classifier(text[:512], candidate_labels)
            
            results.append({
                "text": text,
                "predicted_label": result["labels"][0],
                "confidence": round(result["scores"][0], 4),
                "all_scores": {
                    label: round(score, 4) 
                    for label, score in zip(result["labels"], result["scores"])
                }
            })
        
        return create_success_response({
            "results": results,
            "model_used": model,
            "categories": candidate_labels,
            "task": "classification"
        }, {
            "texts_processed": len(texts),
            "average_confidence": round(sum(r["confidence"] for r in results) / len(results), 4)
        })
    
    except ImportError:
        return create_error_response(
            "Text classification requires transformers library",
            "ImportError",
            {"required_packages": ["transformers", "torch"]}
        )
    except Exception as e:
        logger.error(f"Error in text classification: {e}")
        return create_error_response(
            f"Text classification failed: {str(e)}",
            type(e).__name__
        )


def extract_entities(texts: List[str], model_name: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
    """Extract named entities from texts."""
    
    try:
        # Try spaCy first
        try:
            import spacy
            
            # Load model based on language
            model_map = {
                "en": "en_core_web_sm",
                "de": "de_core_news_sm",
                "fr": "fr_core_news_sm",
                "es": "es_core_news_sm"
            }
            
            model_name = model_name or model_map.get(language, "en_core_web_sm")
            
            try:
                nlp = spacy.load(model_name)
            except OSError:
                # Fallback to English model
                nlp = spacy.load("en_core_web_sm")
            
            results = []
            for text in texts:
                doc = nlp(text)
                
                entities = []
                for ent in doc.ents:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "description": spacy.explain(ent.label_),
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "confidence": getattr(ent, 'confidence', 1.0)
                    })
                
                results.append({
                    "text": text,
                    "entities": entities,
                    "entity_count": len(entities)
                })
            
            return create_success_response({
                "results": results,
                "model_used": model_name,
                "task": "ner"
            }, {
                "texts_processed": len(texts),
                "total_entities": sum(r["entity_count"] for r in results)
            })
        
        except ImportError:
            # Fallback to transformers
            from transformers import pipeline
            
            model = model_name or "dbmdz/bert-large-cased-finetuned-conll03-english"
            ner = pipeline("ner", model=model, aggregation_strategy="simple")
            
            results = []
            for text in texts:
                entities = ner(text[:512])
                
                processed_entities = []
                for entity in entities:
                    processed_entities.append({
                        "text": entity["word"],
                        "label": entity["entity_group"],
                        "confidence": round(entity["score"], 4),
                        "start": entity["start"],
                        "end": entity["end"]
                    })
                
                results.append({
                    "text": text,
                    "entities": processed_entities,
                    "entity_count": len(processed_entities)
                })
            
            return create_success_response({
                "results": results,
                "model_used": model,
                "task": "ner"
            }, {
                "texts_processed": len(texts),
                "total_entities": sum(r["entity_count"] for r in results)
            })
    
    except ImportError:
        return create_error_response(
            "Named entity recognition requires spacy or transformers library",
            "ImportError",
            {"required_packages": ["spacy", "transformers", "torch"]}
        )
    except Exception as e:
        logger.error(f"Error in named entity recognition: {e}")
        return create_error_response(
            f"Named entity recognition failed: {str(e)}",
            type(e).__name__
        )


def summarize_text(texts: List[str], model_name: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
    """Summarize texts."""
    
    try:
        from transformers import pipeline
        
        model = model_name or "facebook/bart-large-cnn"
        summarizer = pipeline("summarization", model=model)
        
        results = []
        for text in texts:
            # Skip very short texts
            if len(text.split()) < 50:
                results.append({
                    "text": text,
                    "summary": text,
                    "compression_ratio": 1.0,
                    "note": "Text too short for summarization"
                })
                continue
            
            # Limit input length
            max_length = min(1024, len(text))
            input_text = text[:max_length]
            
            summary = summarizer(input_text, max_length=150, min_length=30, do_sample=False)
            summary_text = summary[0]["summary_text"]
            
            compression_ratio = len(summary_text) / len(input_text)
            
            results.append({
                "text": text,
                "summary": summary_text,
                "compression_ratio": round(compression_ratio, 4),
                "original_length": len(text),
                "summary_length": len(summary_text)
            })
        
        return create_success_response({
            "results": results,
            "model_used": model,
            "task": "summarization"
        }, {
            "texts_processed": len(texts),
            "average_compression": round(sum(r["compression_ratio"] for r in results) / len(results), 4)
        })
    
    except ImportError:
        return create_error_response(
            "Text summarization requires transformers library",
            "ImportError",
            {"required_packages": ["transformers", "torch"]}
        )
    except Exception as e:
        logger.error(f"Error in text summarization: {e}")
        return create_error_response(
            f"Text summarization failed: {str(e)}",
            type(e).__name__
        )


def extract_keywords(texts: List[str], model_name: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
    """Extract keywords from texts."""
    
    try:
        # Try YAKE first
        try:
            import yake
            
            kw_extractor = yake.KeywordExtractor(
                lan=language,
                n=3,  # n-gram size
                dedupLim=0.7,
                top=10
            )
            
            results = []
            for text in texts:
                keywords = kw_extractor.extract_keywords(text)
                
                processed_keywords = []
                for score, keyword in keywords:
                    processed_keywords.append({
                        "keyword": keyword,
                        "score": round(1 / (1 + score), 4),  # Convert to relevance score
                        "relevance": "high" if score < 0.1 else "medium" if score < 0.5 else "low"
                    })
                
                results.append({
                    "text": text,
                    "keywords": processed_keywords,
                    "keyword_count": len(processed_keywords)
                })
            
            return create_success_response({
                "results": results,
                "extractor": "YAKE",
                "task": "keywords"
            }, {
                "texts_processed": len(texts),
                "total_keywords": sum(r["keyword_count"] for r in results)
            })
        
        except ImportError:
            # Fallback to simple TF-IDF
            from collections import Counter
            import re
            
            # Simple keyword extraction using word frequency
            results = []
            for text in texts:
                # Clean and tokenize
                words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
                
                # Remove common stop words
                stop_words = {
                    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                    'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
                    'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                    'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
                }
                
                filtered_words = [word for word in words if word not in stop_words]
                
                # Count frequency
                word_freq = Counter(filtered_words)
                top_words = word_freq.most_common(10)
                
                keywords = []
                total_words = len(filtered_words)
                for word, count in top_words:
                    score = count / total_words
                    keywords.append({
                        "keyword": word,
                        "score": round(score, 4),
                        "frequency": count,
                        "relevance": "high" if score > 0.05 else "medium" if score > 0.02 else "low"
                    })
                
                results.append({
                    "text": text,
                    "keywords": keywords,
                    "keyword_count": len(keywords)
                })
            
            return create_success_response({
                "results": results,
                "extractor": "Frequency-based",
                "task": "keywords"
            }, {
                "texts_processed": len(texts),
                "total_keywords": sum(r["keyword_count"] for r in results)
            })
    
    except Exception as e:
        logger.error(f"Error in keyword extraction: {e}")
        return create_error_response(
            f"Keyword extraction failed: {str(e)}",
            type(e).__name__
        )


def detect_language(texts: List[str]) -> Dict[str, Any]:
    """Detect language of texts."""
    
    try:
        from langdetect import detect, detect_langs
        
        results = []
        for text in texts:
            try:
                # Detect primary language
                primary_lang = detect(text)
                
                # Get all language probabilities
                lang_probs = detect_langs(text)
                
                probabilities = {}
                for lang_prob in lang_probs:
                    probabilities[lang_prob.lang] = round(lang_prob.prob, 4)
                
                results.append({
                    "text": text,
                    "detected_language": primary_lang,
                    "confidence": probabilities.get(primary_lang, 0),
                    "all_probabilities": probabilities
                })
            
            except Exception as e:
                results.append({
                    "text": text,
                    "detected_language": "unknown",
                    "confidence": 0,
                    "error": str(e)
                })
        
        return create_success_response({
            "results": results,
            "task": "language_detection"
        }, {
            "texts_processed": len(texts),
            "languages_detected": len(set(r["detected_language"] for r in results if r["detected_language"] != "unknown"))
        })
    
    except ImportError:
        return create_error_response(
            "Language detection requires langdetect library",
            "ImportError",
            {"required_packages": ["langdetect"]}
        )
    except Exception as e:
        logger.error(f"Error in language detection: {e}")
        return create_error_response(
            f"Language detection failed: {str(e)}",
            type(e).__name__
        )


def analyze_readability(texts: List[str], language: str = "en") -> Dict[str, Any]:
    """Analyze readability of texts."""
    
    try:
        import textstat
        
        results = []
        for text in texts:
            # Set language for textstat
            if language == "en":
                textstat.set_lang("en")
            
            readability_scores = {
                "flesch_reading_ease": textstat.flesch_reading_ease(text),
                "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
                "gunning_fog": textstat.gunning_fog(text),
                "automated_readability_index": textstat.automated_readability_index(text),
                "coleman_liau_index": textstat.coleman_liau_index(text),
                "linsear_write_formula": textstat.linsear_write_formula(text),
                "dale_chall_readability_score": textstat.dale_chall_readability_score(text)
            }
            
            # Text statistics
            stats = {
                "sentence_count": textstat.sentence_count(text),
                "word_count": textstat.lexicon_count(text),
                "character_count": len(text),
                "syllable_count": textstat.syllable_count(text),
                "avg_sentence_length": textstat.avg_sentence_length(text),
                "avg_syllables_per_word": textstat.avg_syllables_per_word(text)
            }
            
            # Reading level interpretation
            flesch_score = readability_scores["flesch_reading_ease"]
            if flesch_score >= 90:
                reading_level = "Very Easy"
            elif flesch_score >= 80:
                reading_level = "Easy"
            elif flesch_score >= 70:
                reading_level = "Fairly Easy"
            elif flesch_score >= 60:
                reading_level = "Standard"
            elif flesch_score >= 50:
                reading_level = "Fairly Difficult"
            elif flesch_score >= 30:
                reading_level = "Difficult"
            else:
                reading_level = "Very Difficult"
            
            results.append({
                "text": text,
                "readability_scores": {k: round(v, 2) for k, v in readability_scores.items()},
                "text_statistics": stats,
                "reading_level": reading_level,
                "grade_level": round(readability_scores["flesch_kincaid_grade"], 1)
            })
        
        return create_success_response({
            "results": results,
            "task": "readability"
        }, {
            "texts_processed": len(texts),
            "average_grade_level": round(sum(r["grade_level"] for r in results) / len(results), 2)
        })
    
    except ImportError:
        return create_error_response(
            "Readability analysis requires textstat library",
            "ImportError",
            {"required_packages": ["textstat"]}
        )
    except Exception as e:
        logger.error(f"Error in readability analysis: {e}")
        return create_error_response(
            f"Readability analysis failed: {str(e)}",
            type(e).__name__
        )


def detect_toxicity(texts: List[str], model_name: Optional[str] = None) -> Dict[str, Any]:
    """Detect toxicity in texts."""
    
    try:
        from transformers import pipeline
        
        model = model_name or "unitary/toxic-bert"
        classifier = pipeline("text-classification", model=model)
        
        results = []
        for text in texts:
            result = classifier(text[:512])
            
            # Parse result
            if isinstance(result, list) and len(result) > 0:
                prediction = result[0]
                is_toxic = prediction["label"] == "TOXIC"
                confidence = prediction["score"]
            else:
                is_toxic = False
                confidence = 0.0
            
            toxicity_level = "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low"
            
            results.append({
                "text": text,
                "is_toxic": is_toxic,
                "confidence": round(confidence, 4),
                "toxicity_level": toxicity_level if is_toxic else "none"
            })
        
        return create_success_response({
            "results": results,
            "model_used": model,
            "task": "toxicity"
        }, {
            "texts_processed": len(texts),
            "toxic_texts": sum(1 for r in results if r["is_toxic"]),
            "average_confidence": round(sum(r["confidence"] for r in results) / len(results), 4)
        })
    
    except ImportError:
        return create_error_response(
            "Toxicity detection requires transformers library",
            "ImportError",
            {"required_packages": ["transformers", "torch"]}
        )
    except Exception as e:
        logger.error(f"Error in toxicity detection: {e}")
        return create_error_response(
            f"Toxicity detection failed: {str(e)}",
            type(e).__name__
        )


def calculate_similarity(texts: List[str], model_name: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
    """Calculate similarity between texts."""
    
    if len(texts) < 2:
        return create_error_response(
            "Need at least 2 texts for similarity calculation",
            "ValueError",
            {"texts_provided": len(texts)}
        )
    
    try:
        # Try sentence-transformers first
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            model = SentenceTransformer(model_name or 'all-MiniLM-L6-v2')
            embeddings = model.encode(texts)
            
            # Calculate pairwise similarities
            similarity_matrix = cosine_similarity(embeddings)
            
            # Create results
            similarities = []
            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    similarity = similarity_matrix[i][j]
                    similarities.append({
                        "text1_index": i,
                        "text2_index": j,
                        "text1": texts[i],
                        "text2": texts[j],
                        "similarity": round(float(similarity), 4),
                        "similarity_level": "high" if similarity > 0.8 else "medium" if similarity > 0.5 else "low"
                    })
            
            return create_success_response({
                "similarities": similarities,
                "similarity_matrix": similarity_matrix.tolist(),
                "model_used": model_name or 'all-MiniLM-L6-v2',
                "task": "similarity"
            }, {
                "texts_processed": len(texts),
                "comparisons_made": len(similarities),
                "average_similarity": round(np.mean([s["similarity"] for s in similarities]), 4)
            })
        
        except ImportError:
            # Fallback to simple word overlap
            similarities = []
            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    words1 = set(texts[i].lower().split())
                    words2 = set(texts[j].lower().split())
                    
                    intersection = len(words1.intersection(words2))
                    union = len(words1.union(words2))
                    
                    jaccard_similarity = intersection / union if union > 0 else 0
                    
                    similarities.append({
                        "text1_index": i,
                        "text2_index": j,
                        "text1": texts[i],
                        "text2": texts[j],
                        "similarity": round(jaccard_similarity, 4),
                        "similarity_level": "high" if jaccard_similarity > 0.6 else "medium" if jaccard_similarity > 0.3 else "low",
                        "method": "jaccard"
                    })
            
            return create_success_response({
                "similarities": similarities,
                "method": "Jaccard similarity (word overlap)",
                "task": "similarity"
            }, {
                "texts_processed": len(texts),
                "comparisons_made": len(similarities),
                "average_similarity": round(sum(s["similarity"] for s in similarities) / len(similarities), 4)
            })
    
    except Exception as e:
        logger.error(f"Error in similarity calculation: {e}")
        return create_error_response(
            f"Similarity calculation failed: {str(e)}",
            type(e).__name__
        )


def translate_text(texts: List[str], model_name: Optional[str] = None, target_language: str = "en") -> Dict[str, Any]:
    """Translate texts to target language."""
    
    try:
        from transformers import pipeline
        
        # Use a translation model
        model = model_name or "Helsinki-NLP/opus-mt-en-de"  # Example: English to German
        translator = pipeline("translation", model=model)
        
        results = []
        for text in texts:
            translation = translator(text[:512])
            translated_text = translation[0]["translation_text"]
            
            results.append({
                "original_text": text,
                "translated_text": translated_text,
                "target_language": target_language
            })
        
        return create_success_response({
            "results": results,
            "model_used": model,
            "target_language": target_language,
            "task": "translation"
        }, {
            "texts_processed": len(texts)
        })
    
    except ImportError:
        return create_error_response(
            "Translation requires transformers library",
            "ImportError",
            {"required_packages": ["transformers", "torch"]}
        )
    except Exception as e:
        logger.error(f"Error in translation: {e}")
        return create_error_response(
            f"Translation failed: {str(e)}",
            type(e).__name__
        )


def main():
    """Main function for command-line usage."""
    
    parser = argparse.ArgumentParser(
        description="Perform text analysis and ML inference tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sentiment analysis
  python3 text_analysis.py --input '{"text": "I love this product!", "task": "sentiment"}'
  
  # Multiple texts
  python3 text_analysis.py --input '{"text": ["Text 1", "Text 2"], "task": "classification"}'
  
  # Named entity recognition
  python3 text_analysis.py --input '{"text": "John works at Google in New York.", "task": "ner"}'
"""
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', help='JSON input data as string')
    input_group.add_argument('--input-file', help='Path to JSON input file')
    
    # Task options
    parser.add_argument(
        '--task', 
        default='sentiment',
        choices=[
            'sentiment', 'classification', 'ner', 'summarization', 
            'translation', 'keywords', 'similarity', 'language_detection',
            'readability', 'toxicity'
        ],
        help='Analysis task to perform (default: sentiment)'
    )
    
    # Output options
    parser.add_argument('--output-file', help='Path to save output JSON file')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    
    args = parser.parse_args()
    
    try:
        # Parse input data
        if args.input:
            input_data = safe_json_loads(args.input)
        else:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
        
        # Validate input structure
        schema = {
            "text": {"type": ["string", "array"], "required": True},
            "task": {"type": "string", "required": False},
            "model_name": {"type": "string", "required": False},
            "language": {"type": "string", "required": False},
            "batch_size": {"type": "number", "required": False}
        }
        
        validate_input(input_data, schema)
        
        # Extract parameters
        text = input_data["text"]
        task = input_data.get("task", args.task)
        model_name = input_data.get("model_name")
        language = input_data.get("language", "en")
        batch_size = input_data.get("batch_size", 32)
        
        # Perform analysis
        result = analyze_text(
            text=text,
            task=task,
            model_name=model_name,
            language=language,
            batch_size=batch_size
        )
        
        # Output result
        output_json = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)
        
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Results saved to {args.output_file}")
        else:
            print(output_json)
    
    except Exception as e:
        error_result = create_error_response(str(e), type(e).__name__)
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()