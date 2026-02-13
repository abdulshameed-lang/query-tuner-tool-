# Railway Deployment Notes

## Configuration

Railway deployment uses **simplified dependencies** without Oracle support.

### Files Used:
- `requirements.txt` - Simplified dependencies (no Oracle)
- `railway.json` - Railway build configuration
- `Procfile` - Start command

### Files Ignored:
- `Dockerfile.oracle` - Full Docker setup with Oracle (renamed from Dockerfile)
- `requirements/base.txt` - Contains Oracle dependencies

### Environment Variables Required:
```
PORT=8000
ENVIRONMENT=production
SECRET_KEY=<your-secret-key>
DATABASE_URL=sqlite:///./query_tuner.db
CORS_ORIGINS=["https://rare-it-querytime.vercel.app"]
```

### Start Command:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### To Deploy with Full Oracle Support:
Use Docker deployment instead, which uses `Dockerfile.oracle`
