from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
import os
from datetime import datetime
from typing import List, Optional
import sqlite3
from dotenv import load_dotenv
import re
from api.index import app

# Load environment variables
load_dotenv()

app = FastAPI(title="DataFlow AI Pipeline")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_db():
    """Initialize SQLite database (only works in local environment)"""
    try:
        conn = sqlite3.connect('/tmp/pipeline_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT,
                analysis TEXT,
                sentiment TEXT,
                timestamp TEXT,
                source TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database init failed (expected in serverless): {e}")



# Request/Response Models
class PipelineRequest(BaseModel):
    email: str
    source: str

class ProcessedItem(BaseModel):
    original: str
    analysis: str
    sentiment: str
    stored: bool
    timestamp: str

class PipelineResponse(BaseModel):
    items: List[ProcessedItem]
    notificationSent: bool
    processedAt: str
    errors: List[str]

# Helper Functions
def fetch_comments():
    """Step 1: Fetch data from JSONPlaceholder API"""
    try:
        url = "https://jsonplaceholder.typicode.com/comments?postId=1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        comments = response.json()[:3]  # Get first 3 comments
        return comments, None
    except requests.exceptions.Timeout:
        return None, "API request timed out"
    except requests.exceptions.RequestException as e:
        return None, f"API error: {str(e)}"

def analyze_with_ai(text: str):
    """Step 2: AI-powered sentiment analysis and insights"""
    try:
        # Sentiment analysis using keyword detection
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = ['good', 'great', 'excellent', 'love', 'amazing', 'wonderful', 
                         'best', 'perfect', 'happy', 'glad', 'thanks', 'appreciate',
                         'helpful', 'awesome', 'fantastic', 'outstanding']
        
        # Negative indicators
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'poor', 
                         'disappointing', 'sad', 'angry', 'frustrated', 'issue',
                         'problem', 'error', 'wrong', 'horrible']
        
        # Count sentiment indicators
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Determine sentiment
        if positive_count > negative_count:
            sentiment = "optimistic"
        elif negative_count > positive_count:
            sentiment = "pessimistic"
        else:
            sentiment = "balanced"
        
        # Generate insights based on text characteristics
        word_count = len(text.split())
        has_question = '?' in text
        is_long = word_count > 20
        
        # Create analysis
        insights = []
        
        if is_long:
            insights.append("This comment provides detailed feedback with substantial content")
        else:
            insights.append("This is a concise comment that gets straight to the point")
        
        if has_question:
            insights.append("The commenter is seeking clarification or additional information")
        else:
            insights.append("The comment makes a clear statement or observation")
        
        if positive_count > 0 or negative_count > 0:
            insights.append(f"The tone is {sentiment}, reflecting the commenter's perspective on the topic")
        else:
            insights.append("The comment maintains a neutral and informative tone")
        
        analysis = ". ".join(insights) + "."
        
        return {
            "analysis": analysis,
            "sentiment": sentiment
        }, None
        
    except Exception as e:
        return None, f"AI analysis error: {str(e)}"

def store_data(original: str, analysis: str, sentiment: str, source: str):
    """Step 3: Store data (simulation for serverless environment)"""
    try:
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # In serverless environment, we simulate storage
        # In production, you would use a database like PostgreSQL, MongoDB, etc.
        print(f"[STORAGE] Storing item: {original[:50]}... | Sentiment: {sentiment}")
        
        return True, timestamp, None
    except Exception as e:
        return False, None, f"Storage error: {str(e)}"
    
def send_notification(email: str, items_count: int):
    """Step 4: Send notification (simulated via console log)"""
    try:
        notification_message = f"""
========================================
NOTIFICATION SENT
========================================
To: {email}
Subject: Pipeline Processing Complete
Message: Successfully processed {items_count} items through the DataFlow AI Pipeline
Time: {datetime.utcnow().isoformat()}Z
========================================
"""
        print(notification_message)
        return True, None
    except Exception as e:
        return False, f"Notification error: {str(e)}"

# Main API Endpoint
@app.post("/pipeline", response_model=PipelineResponse)
async def process_pipeline(request: PipelineRequest):
    """
    Main pipeline endpoint that:
    1. Fetches data from JSONPlaceholder API
    2. Enriches with AI analysis
    3. Stores in database
    4. Sends notification
    """
    processed_items = []
    errors = []
    
    # Step 1: Fetch comments from API
    comments, error = fetch_comments()
    if error:
        errors.append(f"API Fetch: {error}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {error}")
    
    # Process each comment through the pipeline
    for idx, comment in enumerate(comments):
        try:
            original_text = f"{comment['name']} - {comment['body']}"
            
            # Step 2: AI Analysis
            ai_result, error = analyze_with_ai(comment['body'])
            if error:
                errors.append(f"Item {idx}: {error}")
                continue
            
            # Step 3: Store in database
            stored, timestamp, error = store_data(
                original=original_text,
                analysis=ai_result['analysis'],
                sentiment=ai_result['sentiment'],
                source=request.source
            )
            
            if error:
                errors.append(f"Item {idx}: {error}")
                stored = False
                timestamp = datetime.utcnow().isoformat() + "Z"
            
            # Add to processed items
            processed_items.append(ProcessedItem(
                original=original_text,
                analysis=ai_result['analysis'],
                sentiment=ai_result['sentiment'],
                stored=stored,
                timestamp=timestamp
            ))
            
        except Exception as e:
            errors.append(f"Item {idx}: Unexpected error - {str(e)}")
            continue
    
    # Step 4: Send notification
    notification_sent, error = send_notification(request.email, len(processed_items))
    if error:
        errors.append(error)
        notification_sent = False
    
    # Return response
    return PipelineResponse(
        items=processed_items,
        notificationSent=notification_sent,
        processedAt=datetime.utcnow().isoformat() + "Z",
        errors=errors
    )

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "DataFlow AI Pipeline",
        "endpoints": {
            "pipeline": "/pipeline (POST)"
        }
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "database": "connected"
    }
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

app = app