#!/usr/bin/env python3
"""
Unity AI - Python Worker Script Example
Für Heavy ML/AI Jobs außerhalb von n8n
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

import redis.asyncio as redis
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MLWorker:
    """ML Worker für schwere Berechnungen"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        
    async def connect(self):
        """Redis-Verbindung herstellen"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Redis-Verbindung schließen"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def process_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Job verarbeiten"""
        job_type = job_data.get('type', 'unknown')
        
        logger.info(f"🔄 Processing job: {job_type}")
        
        try:
            if job_type == 'text_clustering':
                return await self.text_clustering(job_data)
            elif job_type == 'data_analysis':
                return await self.data_analysis(job_data)
            elif job_type == 'sentiment_analysis':
                return await self.sentiment_analysis(job_data)
            else:
                raise ValueError(f"Unknown job type: {job_type}")
                
        except Exception as e:
            logger.error(f"❌ Job processing failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def text_clustering(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Text-Clustering mit scikit-learn"""
        texts = job_data.get('texts', [])
        n_clusters = job_data.get('n_clusters', 3)
        
        if not texts:
            raise ValueError("No texts provided for clustering")
        
        # TF-IDF Vectorization
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        X = vectorizer.fit_transform(texts)
        
        # K-Means Clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X)
        
        # Ergebnisse zusammenstellen
        results = {
            'status': 'success',
            'clusters': clusters.tolist(),
            'cluster_centers': kmeans.cluster_centers_.tolist(),
            'n_clusters': n_clusters,
            'inertia': float(kmeans.inertia_),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Text clustering completed: {n_clusters} clusters")
        return results
    
    async def data_analysis(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Datenanalyse mit pandas"""
        data = job_data.get('data', [])
        analysis_type = job_data.get('analysis_type', 'summary')
        
        if not data:
            raise ValueError("No data provided for analysis")
        
        # DataFrame erstellen
        df = pd.DataFrame(data)
        
        results = {
            'status': 'success',
            'analysis_type': analysis_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if analysis_type == 'summary':
            results['summary'] = {
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': df.dtypes.to_dict(),
                'missing_values': df.isnull().sum().to_dict(),
                'numeric_summary': df.describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {}
            }
        elif analysis_type == 'correlation':
            numeric_df = df.select_dtypes(include=[np.number])
            if not numeric_df.empty:
                results['correlation_matrix'] = numeric_df.corr().to_dict()
            else:
                results['correlation_matrix'] = {}
        
        logger.info(f"✅ Data analysis completed: {analysis_type}")
        return results
    
    async def sentiment_analysis(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Einfache Sentiment-Analyse (Mock)"""
        texts = job_data.get('texts', [])
        
        if not texts:
            raise ValueError("No texts provided for sentiment analysis")
        
        # Mock Sentiment Analysis (in Realität: transformers, VADER, etc.)
        sentiments = []
        for text in texts:
            # Einfache Keyword-basierte Sentiment-Erkennung
            positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic']
            negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing', 'poor']
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                sentiment = 'positive'
                score = 0.7 + (positive_count * 0.1)
            elif negative_count > positive_count:
                sentiment = 'negative'
                score = 0.3 - (negative_count * 0.1)
            else:
                sentiment = 'neutral'
                score = 0.5
            
            sentiments.append({
                'text': text,
                'sentiment': sentiment,
                'score': min(max(score, 0.0), 1.0)  # Clamp zwischen 0 und 1
            })
        
        results = {
            'status': 'success',
            'sentiments': sentiments,
            'summary': {
                'total_texts': len(texts),
                'positive': len([s for s in sentiments if s['sentiment'] == 'positive']),
                'negative': len([s for s in sentiments if s['sentiment'] == 'negative']),
                'neutral': len([s for s in sentiments if s['sentiment'] == 'neutral'])
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Sentiment analysis completed: {len(texts)} texts")
        return results
    
    async def listen_for_jobs(self, queue_name: str = "ml_jobs"):
        """Auf Jobs in Redis Queue hören"""
        logger.info(f"🎧 Listening for jobs on queue: {queue_name}")
        
        while True:
            try:
                # Blocking pop von Redis Queue
                result = await self.redis_client.blpop(queue_name, timeout=10)
                
                if result:
                    _, job_json = result
                    job_data = json.loads(job_json)
                    job_id = job_data.get('job_id', 'unknown')
                    
                    logger.info(f"📋 Received job: {job_id}")
                    
                    # Job verarbeiten
                    result = await self.process_job(job_data)
                    
                    # Ergebnis in Results Queue schreiben
                    result['job_id'] = job_id
                    await self.redis_client.lpush(
                        f"{queue_name}_results",
                        json.dumps(result)
                    )
                    
                    logger.info(f"✅ Job completed: {job_id}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing job: {e}")
                await asyncio.sleep(5)  # Kurze Pause bei Fehlern

async def main():
    """Main Worker Loop"""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    queue_name = os.getenv('QUEUE_NAME', 'ml_jobs')
    
    worker = MLWorker(redis_url)
    
    try:
        await worker.connect()
        await worker.listen_for_jobs(queue_name)
    except KeyboardInterrupt:
        logger.info("🛑 Worker stopped by user")
    except Exception as e:
        logger.error(f"❌ Worker error: {e}")
    finally:
        await worker.disconnect()

if __name__ == "__main__":
    asyncio.run(main())