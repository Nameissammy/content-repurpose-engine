# Content Repurpose AI Automation System

![Architecture](architecture.png)

A fully automated system that transforms YouTube videos into platform-specific social media content using AI. The system uses Claude 3.5 Sonnet with LangGraph for intelligent content repurposing, with human-in-the-loop approval before publishing.

## Features

✅ **Automated Content Ingestion** - YouTube video download and transcription
✅ **AI-Powered Repurposing** - LangGraph state machine with Claude 3.5 Sonnet
✅ **Multi-Platform Generation** - Twitter threads, LinkedIn posts, Newsletters
✅ **Human Approval Workflow** - Review and edit content before publishing
✅ **Automated Publishing** - Direct integration with social media APIs
✅ **Scalable Architecture** - Docker, PostgreSQL, Redis, and Celery workers

## Architecture

### Components

1. **Ingestion Layer** - FastAPI webhooks + Celery workers
   - YouTube video metadata extraction (yt-dlp)
   - Transcript fetching from YouTube
   - Metadata extraction

2. **AI Logic Layer** - LangGraph State Machine
   - Context analysis
   - Style guide retrieval
   - Parallel content generation (Twitter/LinkedIn/Newsletter)
   - Quality critique and refinement

3. **Approval System** - React frontend + API
   - Content review dashboard
   - Inline editing
   - Email notifications

4. **Publishing Layer** - Platform-specific publishers
   - Twitter/X API v2
   - LinkedIn API
   - Instagram Graph API
   - Email newsletters (Resend/SendGrid)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- API Keys:
  - Anthropic (Claude)
  - Twitter, LinkedIn, Instagram
  - Resend or SendGrid (email)

### Setup

1. **Clone and configure**
   ```bash
   cd "content repurpose ai automation"
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start services**
   ```bash
   docker-compose up -d
   ```

3. **Run migrations**
   ```bash
   docker-compose exec web alembic upgrade head
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Usage

1. **Submit a YouTube video**
   ```bash
   curl -X POST http://localhost:8000/webhook/youtube \
     -H "Content-Type: application/json" \
     -d '{"video_url": "https://youtube.com/watch?v=VIDEO_ID"}'
   ```

2. **System automatically:**
   - Downloads and transcribes the video
   - Generates content for all platforms
   - Sends email notification

3. **Review in dashboard**
   - Go to http://localhost:5173/approval
   - Review, edit, and approve content

4. **Content publishes automatically**

## Project Structure

```
├── app/
│   ├── ai/                    # LangGraph AI logic
│   │   ├── nodes/            # State machine nodes
│   │   ├── prompts.py        # AI prompts
│   │   └── state_machine.py  # LangGraph workflow
│   ├── api/                   # FastAPI routes
│   ├── models/                # Database models
│   ├── services/              # Business logic
│   │   ├── publishers/       # Platform publishers
│   │   ├── transcription.py
│   │   └── youtube_downloader.py
│   ├── workers/               # Celery tasks
│   ├── config.py
│   ├── database.py
│   └── main.py
├── frontend/                  # React UI
│   └── src/
│       ├── pages/
│       └── App.jsx
├── alembic/                   # Database migrations
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Configuration

### Style Guide

Create custom style guides in the database:

```sql
INSERT INTO style_guide (name, platform, rules, tone, active) VALUES (
  'Technical Founder',
  NULL,
  'Write like a technical founder sharing insights...',
  'conversational',
  true
);
```

### Environment Variables

Key configurations in `.env`:

```bash
# AI
ANTHROPIC_API_KEY=your_key

# Features
ENABLE_AUTO_PUBLISH=false  # Require approval
ENABLE_EMAIL_NOTIFICATIONS=true
MAX_CONCURRENT_JOBS=3
```

## Development

### Run locally without Docker

```bash
# Backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Celery worker
celery -A app.celery_app worker --loglevel=info

# Frontend
cd frontend
npm install
npm run dev
```

### Database migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## API Endpoints

### Webhooks
- `POST /webhook/youtube` - Submit YouTube video

### Content Management
- `GET /api/content/pending` - List pending approvals
- `GET /api/content/{id}` - Get specific content
- `PUT /api/content/{id}` - Update content
- `POST /api/content/{id}/approve` - Approve and publish
- `POST /api/content/{id}/reject` - Reject content

### Dashboard
- `GET /api/dashboard/stats` - Get statistics
- `GET /api/dashboard/recent` - Recent activity

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Database**: PostgreSQL with pgvector
- **Cache/Queue**: Redis, Celery
- **AI**: LangChain, LangGraph, Claude 3.5 Sonnet
- **Frontend**: React 18, Vite, TanStack Query
- **Deployment**: Docker, Docker Compose

## Monitoring

View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f worker
```

Check job queue:
```bash
# Redis CLI
docker-compose exec redis redis-cli
KEYS celery*
```

## Troubleshooting

### Video download fails
- Check FFmpeg installation
- Verify yt-dlp is up to date

### AI generation slow
- Claude API rate limits
- Increase `MAX_CONCURRENT_JOBS`

### Publishing fails
- Verify API credentials
- Check platform API status
- Review error logs

## License

MIT

## Contributing

Pull requests welcome! Please ensure:
- Tests pass
- Code follows style guide
- Documentation updated
