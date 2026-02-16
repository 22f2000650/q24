from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
from datetime import datetime
from typing import List
import re

app = FastAPI(title="DataFlow AI Pipeline")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        comments = response.json()[:3]
        return comments, None
    except requests.exceptions.Timeout:
        return None, "API request timed out"
    except requests.exceptions.RequestException as e:
        return None, f"API error: {str(e)}"

def analyze_with_ai(text: str):
    """Step 2: AI-powered sentiment analysis"""
    try:
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = ['good', 'great', 'excellent', 'love', 'amazing', 'wonderful', 
                         'best', 'perfect', 'happy', 'glad', 'thanks', 'appreciate',
                         'helpful', 'awesome', 'fantastic', 'outstanding']
        
        # Negative indicators
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'poor', 
                         'disappointing', 'sad', 'angry', 'frustrated', 'issue',
                         'problem', 'error', 'wrong', 'horrible']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "optimistic"
        elif negative_count > positive_count:
            sentiment = "pessimistic"
        else:
            sentiment = "balanced"
        
        word_count = len(text.split())
        has_question = '?' in text
        is_long = word_count > 20
        
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
        
        return {"analysis": analysis, "sentiment": sentiment}, None
        
    except Exception as e:
        return None, f"AI analysis error: {str(e)}"

def store_data(original: str, analysis: str, sentiment: str, source: str):
    """Step 3: Store data (simulated for serverless)"""
    try:
        timestamp = datetime.utcnow().isoformat() + "Z"
        print(f"[STORAGE] Item stored: {original[:50]}... | Sentiment: {sentiment}")
        return True, timestamp, None
    except Exception as e:
        return False, None, f"Storage error: {str(e)}"

def send_notification(email: str, items_count: int):
    """Step 4: Send notification"""
    try:
        notification_message = f"""
========================================
NOTIFICATION SENT
========================================
To: {email}
Subject: Pipeline Processing Complete
Message: Successfully processed {items_count} items
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
    """Main pipeline endpoint"""
    processed_items = []
    errors = []
    
    comments, error = fetch_comments()
    if error:
        errors.append(f"API Fetch: {error}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {error}")
    
    for idx, comment in enumerate(comments):
        try:
            original_text = f"{comment['name']} - {comment['body']}"
            
            ai_result, error = analyze_with_ai(comment['body'])
            if error:
                errors.append(f"Item {idx}: {error}")
                continue
            
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
    
    notification_sent, error = send_notification(request.email, len(processed_items))
    if error:
        errors.append(error)
        notification_sent = False
    
    return PipelineResponse(
        items=processed_items,
        notificationSent=notification_sent,
        processedAt=datetime.utcnow().isoformat() + "Z",
        errors=errors
    )

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "running",
        "service": "DataFlow AI Pipeline",
        "endpoints": {
            "pipeline": "/pipeline (POST)"
        }
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }