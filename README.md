# Multi-Tool AI Pipeline for DataFlow Systems

A proof-of-concept data enrichment pipeline demonstrating integration of multiple services.

## Features

- **API Integration**: Fetches comments from JSONPlaceholder API
- **AI Enrichment**: Sentiment analysis and insights
- **Storage**: Data persistence (simulated for serverless)
- **Notifications**: Email notifications

## Local Setup

1. Create virtual environment: `python -m venv venv`
2. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
3. Install: `pip install -r requirements.txt`
4. Run: `python api/index.py`

## API Endpoint

**POST /pipeline**

Request:
```json
{
  "email": "22f2000650@ds.study.iitm.ac.in",
  "source": "JSONPlaceholder Comments"
}
```

Response:
```json
{
  "items": [
    {
      "original": "Comment text...",
      "analysis": "AI analysis...",
      "sentiment": "optimistic/pessimistic/balanced",
      "stored": true,
      "timestamp": "2026-02-16T10:30:00Z"
    }
  ],
  "notificationSent": true,
  "processedAt": "2026-02-16T10:30:05Z",
  "errors": []
}
```

## Deployment

- **GitHub**: https://github.com/22f2000650/q24
- **Vercel**: https://q24-22f2000650.vercel.app

## Testing

```bash
curl -X POST https://q24-22f2000650.vercel.app/pipeline \
  -H "Content-Type: application/json" \
  -d '{"email": "22f2000650@ds.study.iitm.ac.in", "source": "JSONPlaceholder Comments"}'
```

## Author

GitHub: [@22f2000650](https://github.com/22f2000650)