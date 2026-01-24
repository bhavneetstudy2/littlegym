# The Little Gym CRM

A comprehensive multi-tenant CRM system for The Little Gym centers, managing leads, enrollments, attendance, curriculum progress, and renewals.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Alembic
- **Frontend**: Next.js 14+, React, TypeScript, TailwindCSS
- **Infrastructure**: Docker Compose
- **Authentication**: JWT with role-based access control (RBAC)

## Features

- Multi-center support with tenant isolation
- Lead management (Discovery → Intro Visit → Follow-Up → Enrollment)
- Student enrollment with multiple plan types
- Bulk attendance tracking
- Curriculum skill progress tracking
- Automated report card generation
- Renewal alerts and management
- CSV import for data migration
- Role-based access control (Super Admin, Center Admin, Trainer, Counselor)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Littlegym
```

2. Create environment files:
```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.local.example frontend/.env.local
```

3. Start all services:
```bash
docker-compose up
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### First-Time Setup

1. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

2. Create a super admin user (coming soon - seed script)

## Development

### Backend Development

```bash
# Enter backend container
docker-compose exec backend bash

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Frontend Development

```bash
# Enter frontend container
docker-compose exec frontend sh

# Install new dependency
npm install <package-name>
```

## Project Structure

```
c:\Littlegym\
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/v1/         # API endpoints
│   │   ├── core/           # Core utilities (auth, security, database)
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic layer
│   │   └── utils/          # Helper functions
│   └── alembic/            # Database migrations
│
└── frontend/               # Next.js application
    └── src/
        ├── app/            # App Router pages
        ├── components/     # React components
        ├── hooks/          # Custom React hooks
        ├── contexts/       # React contexts
        └── lib/            # Utilities (API client, auth)
```

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

## Database Schema

The system uses 18+ database tables including:
- centers, users
- children, parents, family_links
- leads, intro_visits
- batches, class_sessions
- enrollments, payments, discounts
- attendance
- curricula, skills, skill_progress
- report_cards

See [CLAUDE.md](CLAUDE.md) for detailed schema documentation.

## User Roles

1. **Super Admin**: Manage all centers, global curriculum, cross-center dashboards
2. **Center Admin**: Full access within their center
3. **Trainer**: View assigned batches, mark attendance, update skill progress
4. **Counselor**: Manage leads and follow-ups, schedule intro visits

## License

Proprietary - All rights reserved

## Support

For issues and questions, contact the development team.
