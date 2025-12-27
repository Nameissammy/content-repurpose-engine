# Project File Structure & Details

## Complete File Analysis for Content Repurpose AI Automation System

This document provides a comprehensive breakdown of every file in the project, explaining their purpose, responsibilities, and how they fit into the overall architecture.

---

## 📁 Root Directory

### `.env.example`
**Purpose**: Template for environment variables configuration  
**Details**: 
- Contains all required environment variables for the application
- Includes configurations for:
  - Database (PostgreSQL) connection strings
  - Redis URL for caching and task queue
  - AI/LLM API keys (Anthropic Claude)
  - Social media platform API credentials (Twitter, LinkedIn, Instagram)
  - Email service provider credentials (Resend/SendGrid)
  - Feature flags and limits
  - CORS settings

### `.gitignore`
**Purpose**: Specifies files and directories Git should ignore  
**Details**:
- Python compiled files (*.pyc, __pycache__)
- Virtual environments (venv/, env/)
- Environment variables (.env)
- Database files
- Media files (audio/video downloads)
- IDE configurations
- Docker overrides
- Test coverage reports
- Log files

### `Dockerfile`
**Purpose**: Backend application containerization  
**Details**:
- Base image: Python 3.11-slim
- Installs system dependencies: FFmpeg (for audio processing), PostgreSQL client
- Sets up Python environment with requirements
- Creates upload directory for audio files
- Exposes port 8000 for FastAPI
- Default command: runs Uvicorn server

### `docker-compose.yml`
**Purpose**: Multi-container application orchestration  
**Details**:
- Defines 5 services:
  1. **db**: PostgreSQL with pgvector extension for embeddings
  2. **redis**: Redis cache and Celery message broker
  3. **web**: FastAPI backend application
  4. **worker**: Celery worker for background tasks
  5. **frontend**: React development server
- Configures health checks for database and Redis
- Sets up volume mounts for data persistence and hot-reload
- Manages inter-service dependencies
- Environment variable injection

### `requirements.txt`
**Purpose**: Python dependencies specification  
**Details**:
- **Web Framework**: FastAPI, Uvicorn
- **Database**: SQLAlchemy, Alembic, psycopg2, pgvector
- **Task Queue**: Celery, Redis
- **AI/LLM**: LangChain, LangGraph, Anthropic Claude, OpenAI
- **YouTube Processing**: yt-dlp, youtube-transcript-api
- **Social Media APIs**: Tweepy, linkedin-api, requests
- **Email**: Resend, SendGrid
- **Utilities**: Pydantic, python-dotenv, httpx
- **Testing**: pytest, pytest-asyncio
- **Logging**: structlog

### `alembic.ini`
**Purpose**: Alembic database migration configuration  
**Details**:
- Configures Alembic migration script location
- Sets SQLAlchemy database URL from environment
- Logging configuration for migrations
- Uses dynamic DATABASE_URL from settings

---

## 📁 alembic/

### `env.py`
**Purpose**: Alembic migration environment setup  
**Details**:
- Imports database Base and models for schema detection
- Configures offline and online migration modes
- Overrides database URL from settings
- Sets target metadata from SQLAlchemy models
- Handles both standalone and programmatic execution

### `script.py.mako`
**Purpose**: Template for generating new migration scripts  
**Details**:
- Mako template used by `alembic revision --autogenerate`
- Provides boilerplate for upgrade() and downgrade() functions
- Includes revision tracking and dependency metadata
- Auto-generates imports based on detected changes

### `versions/001_initial_schema.py`
**Purpose**: Initial database schema migration  
**Details**:
- Creates three main tables:
  1. **source_content**: Stores YouTube video metadata and transcripts
     - Fields: video_url, video_id, title, description, duration, audio_path, transcript
     - Embeddings using pgvector for semantic search
     - Status tracking (PENDING, PROCESSING, COMPLETED, FAILED)
  2. **style_guide**: Stores brand voice and writing style guidelines
     - Platform-specific or general style rules
     - Examples, tone, and voice description
  3. **generated_content**: Stores AI-generated platform-specific content
     - Foreign key to source_content
     - Platform enum (TWITTER, LINKEDIN, INSTAGRAM, NEWSLETTER)
     - Approval workflow fields
     - Publishing metadata
- Enables pgvector extension for AI embeddings
- Creates indexes for performance optimization

---

## 📁 app/

### `__init__.py`
**Purpose**: Python package initialization  
**Details**: Empty file marking app as a Python package

### `main.py`
**Purpose**: FastAPI application entry point  
**Details**:
- Creates FastAPI application instance
- Configures structured logging with JSON output
- Sets up CORS middleware for frontend communication
- Registers API routers:
  - `/webhook` - Ingestion webhooks
  - `/api/content` - Content approval/management
  - `/api/dashboard` - Dashboard statistics
- Provides health check and root endpoints
- Startup/shutdown event handlers for logging

### `config.py`
**Purpose**: Application configuration management  
**Details**:
- Uses Pydantic Settings for type-safe configuration
- Loads from .env file automatically
- Configuration categories:
  - Database and Redis URLs
  - Server settings (port, workers, log level)
  - AI API keys (Anthropic)
  - Social media credentials (Twitter, LinkedIn, Instagram)
  - Email provider settings
  - Feature flags (auto-publish, notifications, job limits)
  - Frontend URL for CORS
- Exports singleton `settings` instance

### `database.py`
**Purpose**: Database connection and session management  
**Details**:
- Creates SQLAlchemy engine from DATABASE_URL
- Configures SessionLocal factory for database sessions
- Defines declarative Base for ORM models
- Provides `get_db()` dependency for FastAPI routes
- Ensures proper session cleanup after requests

### `celery_app.py`
**Purpose**: Celery task queue configuration  
**Details**:
- Creates Celery app instance with Redis as broker and backend
- Includes worker modules:
  - ingestion (YouTube processing)
  - content_generation (AI workflow)
  - publishing (social media posting)
  - notifications (email alerts)
- Configuration:
  - JSON serialization
  - UTC timezone
  - 30-minute task time limit
  - Worker prefetch based on MAX_CONCURRENT_JOBS
- Task routing to dedicated queues for isolation

---

## 📁 app/models/

### `__init__.py`
**Purpose**: Model package exports  
**Details**: Exports all models and enums for easy importing

### `source_content.py`
**Purpose**: YouTube video source content model  
**Details**:
- **ContentStatus Enum**: PENDING, PROCESSING, COMPLETED, FAILED
- **SourceContent Model**:
  - Stores video metadata (URL, ID, title, description, duration)
  - Transcript text from YouTube
  - Audio file path (optional, for backward compatibility)
  - pgvector embedding for semantic search (1536 dimensions)
  - JSON metadata field for additional info
  - Status tracking and error messages
  - Timestamps (created_at, updated_at, processed_at)
  - Unique constraints on video_url and video_id

### `generated_content.py`
**Purpose**: AI-generated platform-specific content model  
**Details**:
- **Platform Enum**: TWITTER, LINKEDIN, INSTAGRAM, NEWSLETTER
- **ApprovalStatus Enum**: PENDING_APPROVAL, APPROVED, REJECTED, PUBLISHED, FAILED
- **GeneratedContent Model**:
  - Foreign key to source_content
  - Platform identifier
  - Generated content text
  - Content parts for multi-part posts (Twitter threads)
  - Media URLs for images/videos
  - Approval workflow (status, approver, timestamp)
  - Publishing metadata (URL, timestamp)
  - Error tracking and retry count
  - Timestamps

### `style_guide.py`
**Purpose**: Brand voice and style guidelines model  
**Details**:
- Stores writing style rules and examples
- Can be platform-specific or general (NULL platform)
- Fields:
  - name (unique identifier)
  - platform (optional platform targeting)
  - rules (markdown/text style guidelines)
  - examples (JSON array of example posts)
  - tone (e.g., "professional", "casual", "technical")
  - voice_description (detailed voice guidelines)
  - active flag (for enabling/disabling)
  - Timestamps

---

## 📁 app/api/

### `webhooks.py`
**Purpose**: Webhook endpoints for content ingestion  
**Details**:
- **POST /webhook/youtube**: Accept YouTube video URLs
  - Validates URL format and extracts video ID
  - Checks for duplicate videos
  - Creates SourceContent record
  - Triggers async ingestion Celery task
  - Returns job ID for tracking
- **GET /webhook/status/{job_id}**: Check ingestion job status
  - Queries Celery task state
  - Returns task result if completed
- Uses regex patterns to extract YouTube video IDs from various URL formats
- Structured logging for all operations

### `approval.py`
**Purpose**: Content approval and management API  
**Details**:
- **GET /api/content/pending**: List all pending approval content
  - Joins with source_content for video metadata
  - Filters by PENDING_APPROVAL status
  - Returns content with video title and URL
- **GET /api/content/{id}**: Get specific content by ID
  - Retrieves content with source video information
- **PUT /api/content/{id}**: Update/edit content
  - Allows editing content text and parts
  - Maintains audit trail
- **POST /api/content/{id}/approve**: Approve and trigger publishing
  - Updates approval status and metadata
  - Triggers publishing Celery task
- **POST /api/content/{id}/reject**: Reject content
  - Marks content as rejected
- Pydantic models for request/response validation

### `dashboard.py`
**Purpose**: Dashboard statistics and analytics API  
**Details**:
- **GET /api/dashboard/stats**: Aggregate statistics
  - Video counts by status (total, pending, processing, completed)
  - Content counts by approval status
  - Success rate calculations
  - Uses SQLAlchemy aggregate functions
- **GET /api/dashboard/recent**: Recent activity
  - Lists recent videos and generated content
  - Configurable limit (default 10)
  - Returns with metadata for UI display

---

## 📁 app/services/

### `transcription.py`
**Purpose**: YouTube transcript fetching service  
**Details**:
- Uses `youtube-transcript-api` library
- Fetches transcripts directly from YouTube (no audio download needed)
- Prefers manually created transcripts over auto-generated
- Falls back to auto-generated if manual unavailable
- Returns:
  - Full transcript text
  - Language code
  - Timestamped segments with start/end times
- Handles errors (TranscriptsDisabled, NoTranscriptFound)
- Structured logging with word count and segment count

### `youtube_downloader.py`
**Purpose**: YouTube video metadata and audio download  
**Details**:
- Uses yt-dlp for YouTube interaction
- **get_metadata()**: Fetches video info without downloading
  - Returns: title, description, duration, uploader, view count, like count
- **download_audio()**: Downloads audio as MP3 (optional, backward compatibility)
  - Uses FFmpeg for audio extraction
  - Saves to uploads/audio directory
  - Returns metadata + audio file path
- **cleanup()**: Removes downloaded audio files
- Configurable output directory
- Structured logging for all operations

---

## 📁 app/services/publishers/

### `twitter_publisher.py`
**Purpose**: Twitter/X publishing integration  
**Details**:
- Uses Tweepy library with Twitter API v2
- Authenticates with OAuth 2.0 (bearer token + consumer keys)
- **publish_thread()**: Posts Twitter thread
  - Accepts list of tweet texts
  - Posts first tweet
  - Replies subsequent tweets to create thread
  - Validates 280 character limit
  - Returns thread URL and tweet IDs
- Rate limit handling enabled
- Structured logging for each tweet

### `linkedin_publisher.py`
**Purpose**: LinkedIn publishing integration  
**Details**:
- Uses LinkedIn REST API v2
- **get_user_urn()**: Retrieves authenticated user's URN
- **publish_post()**: Creates LinkedIn post
  - Builds UGC (User Generated Content) payload
  - Sets visibility to PUBLIC
  - Supports text-only posts
  - Media support (simplified, needs image upload implementation)
  - Returns post ID and URL
- Uses authorization bearer token
- X-Restli-Protocol-Version 2.0.0 header

### `instagram_publisher.py`
**Purpose**: Instagram publishing integration  
**Details**:
- Uses Instagram Graph API
- **publish_post()**: Two-step Instagram publishing
  1. Create media container with caption and image URL
  2. Publish container to feed
- Requires:
  - Business account ID
  - Publicly accessible image URL
  - Access token
- Returns post ID and URL
- Notes requirement for image (Instagram doesn't support text-only)

### `newsletter_publisher.py`
**Purpose**: Email newsletter publishing  
**Details**:
- Supports multiple email providers: Resend and SendGrid
- **publish_newsletter()**: Send HTML email
  - Accepts subject, HTML content, recipient list
  - Routes to appropriate provider
- **_send_resend()**: Resend implementation
  - Uses Resend SDK
  - Returns email ID
- **_send_sendgrid()**: SendGrid implementation
  - Uses SendGrid SDK
  - Returns message ID and status code
- Defaults to sending to FROM_EMAIL for testing

---

## 📁 app/workers/

### `ingestion.py`
**Purpose**: Celery worker for YouTube video ingestion  
**Details**:
- **DatabaseTask**: Base class providing database session management
- **ingest_video(source_id)**: Main ingestion task
  - Updates status to PROCESSING
  - Step 1: Fetches video metadata (yt-dlp)
  - Step 2: Fetches transcript from YouTube
  - Step 3: Updates database with all information
  - Step 4: Triggers content_generation worker
  - Stores metadata JSON (uploader, view count, language, segments)
  - Marks status as COMPLETED or FAILED
  - Retry logic with exponential backoff (3 max retries)
- Structured logging throughout workflow

### `content_generation.py`
**Purpose**: Celery worker for AI content generation  
**Details**:
- **generate_content(source_id)**: Main generation task
  - Fetches source content with transcript
  - Prepares video metadata
  - Runs LangGraph AI workflow
  - Saves generated content for each platform:
    - Twitter (with thread parts as JSON)
    - LinkedIn
    - Newsletter (with subject line in metadata)
  - Creates GeneratedContent records with PENDING_APPROVAL status
  - Triggers notification worker for each content piece
  - Retry logic (2 max retries)
- Uses DatabaseTask base for session management

### `publishing.py`
**Purpose**: Celery worker for social media publishing  
**Details**:
- **publish_content(content_id)**: Main publishing task
  - Validates content is APPROVED
  - Routes to platform-specific publishers:
    - _publish_twitter(): Parses thread JSON and posts
    - _publish_linkedin(): Posts with optional media
    - _publish_instagram(): Requires image URL
    - _publish_newsletter(): Extracts subject from metadata
  - Updates content status to PUBLISHED
  - Stores published URL
  - Error handling with FAILED status
  - Retry logic with exponential backoff (3 max retries)
- Platform-specific error handling

### `notifications.py`
**Purpose**: Celery worker for email notifications  
**Details**:
- **send_approval_notification(content_id)**: Send approval request email
  - Checks ENABLE_EMAIL_NOTIFICATIONS feature flag
  - Fetches content and source video info
  - Builds HTML email with:
    - Video title and platform
    - Content preview (first 500 chars)
    - Review button linking to frontend
  - Routes to email provider (Resend or SendGrid)
  - Sends to FROM_EMAIL (admin self-notification)
- Helper functions for each email provider
- Structured logging

---

## 📁 app/ai/

### `prompts.py`
**Purpose**: AI prompt templates for content generation  
**Details**:
- **CONTEXT_ANALYZER_PROMPT**: Analyzes video transcript
  - Extracts main topic, key insights, quotes
  - Identifies target audience and tone
  - Provides structured analysis for content creation
- **STYLE_GUIDE_TEMPLATE**: Formats style guide for AI
  - Includes rules, tone, voice, examples
- **TWITTER_GENERATOR_PROMPT**: Creates Twitter threads
  - 5-8 tweet format
  - Hook + insights + CTA structure
  - Emoji usage guidelines
  - 280 character limit enforcement
- **LINKEDIN_GENERATOR_PROMPT**: Creates LinkedIn posts
  - 1300-2000 character professional posts
  - Story-driven structure
  - Key takeaways format
  - Hashtag guidelines
- **NEWSLETTER_GENERATOR_PROMPT**: Creates email newsletters
  - Subject line + structured body
  - Educational tone
  - 400-600 words
  - Markdown formatting
- **CRITIC_PROMPT**: Reviews and refines content
  - Checks factual accuracy, style compliance, engagement
  - Returns APPROVE/REVISE verdict with specific feedback
- Includes few-shot examples for Twitter and LinkedIn

### `state_machine.py`
**Purpose**: LangGraph state machine orchestration  
**Details**:
- **ContentState**: TypedDict defining workflow state
  - Input: transcript, metadata
  - Analysis: context_analysis, style_guide
  - Generated: platform-specific content (Twitter, LinkedIn, Newsletter)
  - Refined: critiqued and improved versions
- **Node Functions**:
  - analyze_node: Runs context analysis
  - style_node: Retrieves style guide from database
  - twitter_node: Generates Twitter content
  - linkedin_node: Generates LinkedIn content
  - newsletter_node: Generates newsletter content
  - critique_twitter_node: Reviews Twitter content
  - critique_linkedin_node: Reviews LinkedIn content
  - critique_newsletter_node: Reviews newsletter content
- **Workflow Structure**:
  1. Analyze transcript → 2. Retrieve style → 3. Generate (parallel) → 4. Critique (parallel)
- **run_content_generation()**: Main entry point
  - Initializes state with transcript and metadata
  - Invokes compiled workflow
  - Returns refined content for all platforms
- Uses LangGraph for parallel execution

---

## 📁 app/ai/nodes/

### `context_analyzer.py`
**Purpose**: First AI node - transcript analysis  
**Details**:
- Uses Claude 3.5 Sonnet
- Analyzes video transcript to extract:
  - Main topic and thesis
  - Key value propositions
  - Memorable quotes
  - Target audience
  - Core takeaways
  - Emotional tone
- Includes video title and description in context
- Temperature: 0.3 (lower for analytical accuracy)
- Max tokens: 2000
- Returns structured analysis for downstream nodes

### `style_retriever.py`
**Purpose**: Retrieves brand style guidelines from database  
**Details**:
- Queries StyleGuide table for active guides
- Supports platform-specific or general style guides
- Falls back to general guide if platform-specific unavailable
- Returns default style if no guide found:
  - "Create engaging, authentic content"
  - Conversational tone
  - Knowledgeable but approachable voice
- Formats style guide using template from prompts.py
- Returns both formatted guide and individual components

### `twitter_generator.py`
**Purpose**: Generates Twitter thread content  
**Details**:
- Uses Claude 3.5 Sonnet
- Creates 5-8 tweet thread
- Parses tweets split by "---TWEET---" delimiter
- Validates 280 character limit per tweet
- Truncates with "..." if over limit
- Temperature: 0.7 (higher for creative content)
- Max tokens: 2500
- Returns:
  - Full thread as single string
  - Individual tweets as JSON array (content_parts)
  - Tweet count
- Structured logging with validation warnings

### `linkedin_generator.py`
**Purpose**: Generates LinkedIn post content  
**Details**:
- Uses Claude 3.5 Sonnet
- Creates 1300-2000 character professional post
- Extracts hashtags from generated content
  - Separates hashtags from main content
  - Adds hashtags at end of post
- Temperature: 0.7
- Max tokens: 3000
- Returns:
  - Post content with hashtags
  - Character count
  - Extracted hashtag list
- Professional storytelling format

### `newsletter_generator.py`
**Purpose**: Generates email newsletter content  
**Details**:
- Uses Claude 3.5 Sonnet
- Creates newsletter with subject line + body
- Parses subject line from output:
  - Looks for "Subject Line:" or "Subject:" prefix
  - Separates subject from body content
- Temperature: 0.7
- Max tokens: 3500
- Returns:
  - Newsletter body content
  - Subject line
  - Word count
- Educational, well-structured email format

### `critic.py`
**Purpose**: Quality control and content refinement  
**Details**:
- Second LLM pass for quality assurance
- Uses Claude 3.5 Sonnet
- Reviews generated content against:
  - Factual accuracy
  - Style guide compliance
  - Engagement potential
  - Platform optimization
  - Grammar and clarity
- Temperature: 0.2 (lower for analytical review)
- Max tokens: 3000
- Parses verdict from response:
  - VERDICT: APPROVE or REVISE
  - ISSUES: List of problems found
  - REVISED_CONTENT: Improved version if needed
- Returns original content on errors (graceful degradation)
- Structured logging with verdict details

---

## 📁 frontend/

### `index.html`
**Purpose**: React app HTML entry point  
**Details**:
- Standard React SPA structure
- Includes root div for React mount
- References Vite SVG icon
- Sets page title: "Content Repurpose AI"
- Loads main.jsx module script

### `package.json`
**Purpose**: Frontend dependencies and scripts  
**Details**:
- **Dependencies**:
  - React 18.2.0 (UI library)
  - React Router DOM (routing)
  - TanStack Query (data fetching/caching)
  - Axios (HTTP client)
- **Dev Dependencies**:
  - Vite (build tool)
  - Vite React plugin
  - TypeScript types
- **Scripts**:
  - dev: Run development server
  - build: Production build
  - preview: Preview production build

### `vite.config.js`
**Purpose**: Vite build tool configuration  
**Details**:
- Uses React plugin for JSX transformation
- Server configuration:
  - Host: true (accessible externally)
  - Port: 5173
  - Proxy configuration for API requests:
    - /api → http://web:8000
    - /webhook → http://web:8000
  - Enables seamless API communication in Docker

### `Dockerfile`
**Purpose**: Frontend container configuration  
**Details**:
- Base: Node 18 Alpine (lightweight)
- Installs npm dependencies
- Copies source code
- Exposes port 5173
- Runs dev server with --host flag for Docker networking

### `src/main.jsx`
**Purpose**: React application bootstrap  
**Details**:
- Imports React and ReactDOM
- Creates TanStack Query client for data fetching
- Wraps App in QueryClientProvider for global query state
- Uses React.StrictMode for development checks
- Mounts to #root element

### `src/index.css`
**Purpose**: Global CSS styles and design system  
**Details**:
- **CSS Variables** (Design Tokens):
  - Dark mode color palette
  - Spacing scale (xs to xl)
  - Border radius values
  - Typography (Inter font)
  - Accent colors with gradients
  - Status colors (success, warning, error)
- **Glassmorphism** styling
  - Semi-transparent backgrounds
  - Backdrop blur effects
  - Subtle borders and shadows
- **Component Styles**:
  - Gradient buttons (.btn-primary)
  - Secondary buttons
  - Input/textarea styling with focus states
  - Status badges
  - Loading spinner
- **Animations**:
  - Fade-in animation
  - Spin animation for loader
- **Custom Scrollbar** styling
- Modern, premium dark UI design

### `src/App.jsx`
**Purpose**: Main application component and routing  
**Details**:
- Sets up React Router with BrowserRouter
- **Layout**:
  - Sidebar navigation (250px fixed width)
  - Main content area (flex-grow)
- **Navigation**:
  - Dashboard (/)
  - Approval Queue (/approval)
  - Content Editor (/approval/:id)
- **NavLink Component**:
  - Custom link with hover effects
  - Active state styling
  - Smooth transitions
- Gradient logo text with WebKit background clip

---

## 📁 frontend/src/pages/

### `Dashboard.jsx`
**Purpose**: Main dashboard overview page  
**Details**:
- **Data Fetching**: TanStack Query for /api/dashboard/stats
- **Components**:
  - StatCard: Displays key metrics with optional highlight
  - StatusRow: Shows status breakdowns
- **Metrics Displayed**:
  - Total videos (with processing count)
  - Generated content (with published count)
  - Pending approval (highlighted)
  - Success rate (calculated from approved + published / total)
- **Layout**:
  - Responsive grid for stat cards
  - Detailed breakdown in glass card
  - Split view: Videos vs Content status
- Loading spinner during data fetch
- Fade-in animation on load

### `ApprovalList.jsx`
**Purpose**: Content approval queue listing  
**Details**:
- **Data Fetching**: TanStack Query for /api/content/pending
- **ContentCard Component**:
  - Platform icon with color coding:
    - Twitter: #1DA1F2 (𝕏)
    - LinkedIn: #0A66C2 (in)
    - Instagram: #E4405F (📷)
    - Newsletter: #10b981 (📧)
  - Source video title
  - Content preview (truncated to 3 lines)
  - Creation date
  - "Review & Approve" button
  - Hover effects (border highlight, translateY)
  - Clickable card navigates to editor
- **Empty State**: "No content pending approval" message
- **Header**: Shows pending count badge
- Responsive grid layout

### `ContentEditor.jsx`
**Purpose**: Content review and editing page  
**Details**:
- **Data Fetching**:
  - GET /api/content/{id} for content details
  - Loads into editable state
- **Mutations**:
  - PUT /api/content/{id} - Save changes
  - POST /api/content/{id}/approve - Approve and publish
  - POST /api/content/{id}/reject - Reject content
- **Layout** (2-column grid):
  - Left: Source video info
    - Video title
    - YouTube link
    - Platform badge
  - Right: Content editor
    - Large textarea (15 rows, monospace font)
    - Save Changes button
    - Reject button (red text)
    - Approve & Publish button (primary)
- **Preview Section**: Shows formatted content below
- **Navigation**: Back to Queue button
- **Confirmations**: Uses browser confirm() for approve/reject
- Query invalidation after mutations
- Disabled states during pending mutations

---

## Project Architecture Summary

### Technology Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Database**: PostgreSQL 16 with pgvector extension
- **Cache/Queue**: Redis 7, Celery
- **AI**: Anthropic Claude 3.5 Sonnet, LangChain, LangGraph
- **Frontend**: React 18, Vite, TanStack Query
- **Deployment**: Docker, Docker Compose

### Data Flow
1. **Ingestion**: YouTube URL → webhook → Celery task → metadata + transcript → database
2. **Generation**: Source content → LangGraph workflow → Claude AI → multi-platform content → database
3. **Approval**: Frontend fetches → user reviews/edits → approve → triggers publishing
4. **Publishing**: Celery task → platform publishers → posted content → URL stored

### Key Design Patterns
- **Repository Pattern**: Models separate from business logic
- **Service Layer**: Encapsulated business logic in services/
- **Task Queue**: Async processing with Celery workers
- **State Machine**: LangGraph for AI workflow orchestration
- **Dependency Injection**: FastAPI dependencies for DB sessions
- **Factory Pattern**: SessionLocal for database sessions

### Scalability Features
- Separate worker queues (ingestion, generation, publishing, notifications)
- Concurrent job limiting via MAX_CONCURRENT_JOBS
- Database connection pooling
- Redis-backed result storage
- Horizontal scaling via Docker Compose replicas
- Retry logic with exponential backoff

---

## File Count Summary
- **Root Configuration**: 6 files
- **Alembic Migrations**: 3 files
- **Backend (app/)**: 5 core files
- **Models**: 4 files
- **API Routes**: 3 files
- **Services**: 6 files
- **Workers**: 4 files
- **AI System**: 8 files
- **Frontend**: 10 files
- **Total**: ~49 source files (excluding .git, node_modules, venv)

---

*This documentation provides a complete reference for understanding the project structure, file purposes, and system architecture. Each file plays a specific role in the content repurposing pipeline from YouTube video ingestion to multi-platform social media publishing.*
