# Project Management System Documentation

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Features](#features)
4. [Architecture](#architecture)
5. [API Documentation](#api-documentation)
6. [Database Schema](#database-schema)
7. [User Roles](#user-roles)
8. [Modules](#modules)

## Overview
The Project Management System is a comprehensive web application built with Flask that enables organizations to manage projects, tasks, and teams efficiently. The system provides features like Eisenhower matrices for task prioritization, performance tracking, and advanced project analytics.

## Installation
```bash
# Clone the repository
git clone <repository-url>

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db upgrade

# Run the application
python run.py
```

## Features
1. **Project Management**
   - Create and manage projects
   - Track project progress
   - Set project deadlines
   - Assign team members
   - Project analytics and reporting

2. **Task Management**
   - Task creation and assignment
   - Task prioritization using Eisenhower Matrix
   - Task dependencies
   - Task comments and ratings
   - Task status tracking

3. **Team Management**
   - User roles (Admin, Project Manager, Team Member)
   - Team creation and management
   - Resource allocation
   - Performance tracking
   - Workload monitoring

4. **Analytics & Reporting**
   - Project progress tracking
   - Team performance metrics
   - Resource utilization reports
   - Milestone tracking
   - Risk assessment

## Architecture
The application follows an MVC (Model-View-Controller) architecture:

```plaintext
project_management/
├── app/
│   ├── models/         # Database models
│   ├── routes/         # Route handlers
│   ├── templates/      # HTML templates
│   ├── static/         # Static files (CSS, JS)
│   └── services/       # Business logic
├── migrations/         # Database migrations
└── tests/             # Unit tests
```

## API Documentation

### Authentication Endpoints
- POST `/auth/login`: User login
- POST `/auth/register`: User registration
- POST `/auth/logout`: User logout

### Project Endpoints
- GET `/projects`: List all projects
- POST `/project/create`: Create new project
- GET `/project/<id>`: Get project details
- PUT `/project/<id>`: Update project
- DELETE `/project/<id>`: Delete project

### Task Endpoints
- GET `/tasks`: List all tasks
- POST `/task/create`: Create new task
- PUT `/task/<id>/status`: Update task status
- POST `/task/<id>/comment`: Add task comment
- POST `/task/<id>/rate`: Rate task

## Database Schema

### Core Tables
1. **users**
   - id (PK)
   - username
   - email
   - password
   - role
   - department_id (FK)

2. **projects**
   - id (PK)
   - name
   - description
   - status
   - created_by (FK)
   - created_at
   - deadline

3. **tasks**
   - id (PK)
   - title
   - description
   - status
   - project_id (FK)
   - assigned_to (FK)
   - due_date

### Supporting Tables
- departments
- team_members
- comments
- ratings
- task_dependencies
- project_milestones

## User Roles

### Administrator
- Full system access
- User management
- Department management
- System configuration

### Project Manager
- Project creation and management
- Team assignment
- Resource allocation
- Performance monitoring
- Report generation

### Team Member
- Task management
- Time tracking
- Project collaboration
- Status updates

## Modules

### 1. Project Module
```python
class Project:
    """
    Handles project-related operations including:
    - Project creation
    - Progress tracking
    - Team assignment
    - Milestone management
    """
```

### 2. Task Module
```python
class Task:
    """
    Manages task operations:
    - Task creation and assignment
    - Status updates
    - Dependencies
    - Time tracking
    """
```

### 3. User Module
```python
class User:
    """
    Handles user-related functionality:
    - Authentication
    - Role management
    - Profile management
    - Performance tracking
    """
```

### 4. Reporting Module
```python
class ReportingService:
    """
    Generates various reports:
    - Project progress
    - Team performance
    - Resource utilization
    - Time tracking
    """
```

## Security
- Password hashing using SHA-256
- Role-based access control
- CSRF protection
- Session management
- Input validation

## Best Practices
1. Follow PEP 8 style guide
2. Write unit tests for new features
3. Document code changes
4. Use meaningful commit messages
5. Perform code reviews

## Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Create pull request
5. Wait for review

## License
MIT License - See LICENSE file for details
