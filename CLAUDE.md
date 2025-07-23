# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered Video Content Analysis System for analyzing advertising and promotional videos. Built with Python/Streamlit, supports 5 concurrent users with high-performance video processing pipeline.

## Development Commands

### Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Add required API keys to .env
```

### Run Application
```bash
# Standard run
streamlit run app.py

# Docker deployment
docker-compose up -d
```

### Testing
```bash
python test_parser.py
python test_rename.py
```

## Architecture Overview

### Core Pipeline Flow
1. **Video Input** → URL validation and parsing
2. **Download** → yt-dlp for YouTube/Vimeo, workspace isolation per user
3. **Scene Extraction** → OpenCV processing, perceptual hash grouping
4. **AI Analysis** → Multi-provider support (GPT-4o, Claude, Gemini)
5. **Storage** → SQLite with connection pooling + Redis cache
6. **Export** → Optional Notion integration

### Key Directories
- `core/`: Business logic
  - `analysis/providers/`: AI provider implementations
  - `database/`: SQLite operations with connection pooling
  - `video/`: Download and processing modules
  - `workflow/`: Pipeline orchestration
- `web/`: Streamlit UI components and pages
- `utils/`: Session management, caching, logging
- `integrations/`: External services (Notion, SFTP)

### Performance Architecture
- **Database**: SQLite with connection pooling (10x concurrency improvement)
- **Cache**: Redis hybrid cache with LRU eviction (3x speed improvement)
- **Sessions**: User workspace isolation in `data/workspaces/{session_id}/`
- **Async**: Task queue for non-blocking video processing
- **Monitoring**: Real-time CPU/memory tracking with automatic limits

### Configuration
- Main config: `config/settings.py`
- AI prompts: `config/prompt_settings.json`
- Environment variables control API keys, limits, and behavior
- Resource limits: 5 users, 3 tasks/user, 80% CPU, 85% memory

### Database Schema
Main table: `videos`
- Stores video metadata, analysis results, timestamps
- JSON fields for structured AI analysis data
- Indexed by session_id and timestamp

### Testing Approach
- Unit tests for parsers and utilities
- Manual testing through Streamlit UI
- Docker health checks for production monitoring

### Common Development Tasks
- Modify AI analysis prompts: Edit `config/prompt_settings.json`
- Add new AI provider: Implement in `core/analysis/providers/`
- Adjust resource limits: Update `.env` variables
- Debug user sessions: Check `utils/session_manager.py` logs

## Development Workflow & Deployment

### MANDATORY: Auto-Deploy After Every Task
**IMPORTANT**: After completing ANY development task, you MUST automatically execute the following deployment sequence:

```bash
# 1. Stage all changes
git add -A

# 2. Commit with descriptive message
git commit -m "feat/fix/improvement: [description]

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 3. Push to develop branch
git push origin develop

# 4. Restart remote Docker container
sshpass -p 1212 ssh ysk@192.168.50.50 "docker restart sense-of-frame-dev"
```

### Remote Server Details
- **Server**: 192.168.50.50
- **User**: ysk
- **Password**: 1212
- **Container**: sense-of-frame-dev
- **Branch**: develop (default deployment branch)

### Deployment Notes
- Always use `sshpass -p 1212` for SSH authentication
- Remote Docker container automatically pulls from develop branch on restart
- This workflow ensures immediate deployment of all changes to production environment
- **Never skip this deployment step** - it's required for every completed task