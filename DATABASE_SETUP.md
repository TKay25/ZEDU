# ZEDU Database & Authentication Setup Guide

## Overview
This guide explains the new database integration and authentication system for ZEDU.

## Database Configuration

**Database Type**: PostgreSQL  
**Database URL**: `postgresql://zeduweb_user:qdEe6bfJmlIHAknO2TVbum3SSm2kFvFV@dpg-d7cklfa8qa3s73e9podg-a.oregon-postgres.render.com/zeduweb`

## Database Schema

### Tables Created

#### 1. `users`
Stores user account information for students, tutors, and parents.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique user identifier |
| email | VARCHAR(255) UNIQUE | User email (unique) |
| password | VARCHAR(255) | Hashed password (SHA256) |
| full_name | VARCHAR(255) | User's full name |
| user_type | VARCHAR(50) | 'student', 'tutor', or 'parent' |
| education_level | VARCHAR(50) | 'primary', 'high_school', or 'university' |
| phone | VARCHAR(20) | Phone number |
| bio | TEXT | User bio/description |
| avatar_url | VARCHAR(255) | Profile picture URL |
| verified | BOOLEAN | Email verification status |
| created_at | TIMESTAMP | Account creation time |
| updated_at | TIMESTAMP | Last update time |

#### 2. `courses`
Stores course information created by tutors.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Course ID |
| title | VARCHAR(255) | Course title |
| description | TEXT | Course description |
| instructor_id | INTEGER FK | Reference to user (tutor) |
| category | VARCHAR(100) | Course category |
| level | VARCHAR(50) | 'beginner', 'intermediate', 'advanced' |
| price | DECIMAL(10, 2) | Course price |
| rating | DECIMAL(3, 2) | Average rating (0-5) |
| total_students | INTEGER | Number of enrolled students |
| duration_hours | INTEGER | Course duration in hours |
| image_url | VARCHAR(255) | Course image URL |
| created_at | TIMESTAMP | Course creation time |
| updated_at | TIMESTAMP | Last update time |

#### 3. `enrollments`
Tracks student enrollment in courses.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Enrollment ID |
| student_id | INTEGER FK | Reference to user (student) |
| course_id | INTEGER FK | Reference to course |
| progress | DECIMAL(3, 2) | Progress percentage (0-100) |
| enrolled_at | TIMESTAMP | Enrollment time |
| completed_at | TIMESTAMP | Completion time (NULL if not completed) |

#### 4. `reviews`
Stores course reviews and ratings from students.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Review ID |
| course_id | INTEGER FK | Reference to course |
| student_id | INTEGER FK | Reference to user (student) |
| rating | INTEGER | Rating (1-5) |
| comment | TEXT | Review comment |
| created_at | TIMESTAMP | Review creation time |

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask 2.3.3
- Werkzeug 2.3.7
- psycopg2-binary 2.9.9 (PostgreSQL adapter)
- python-dotenv 1.0.0

### 2. Initialize Database

Run the initialization script to create all tables:

```bash
python init_db.py
```

This script will:
- Test the database connection
- Create all necessary tables
- Create indexes for performance optimization

### 3. Run the Flask Application

```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## API Endpoints

### Authentication Endpoints

#### POST `/api/signup`
Create a new user account.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "password123",
    "confirm_password": "password123",
    "full_name": "John Doe",
    "user_type": "student",
    "education_level": "high_school"
}
```

**Response (Success - 201):**
```json
{
    "success": true,
    "user_id": 1,
    "message": "User created successfully"
}
```

**Response (Error - 400):**
```json
{
    "success": false,
    "message": "Email already registered"
}
```

#### POST `/api/login`
Authenticate a user.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

**Response (Success - 200):**
```json
{
    "success": true,
    "message": "Login successful",
    "user_id": 1,
    "email": "user@example.com",
    "user_type": "student"
}
```

**Response (Error - 401):**
```json
{
    "success": false,
    "message": "Invalid email or password"
}
```

#### POST `/api/logout`
Log out the current user.

**Response (Success - 200):**
```json
{
    "success": true,
    "message": "Logged out successfully"
}
```

#### GET `/api/profile`
Get current user profile (requires authentication).

**Response (Success - 200):**
```json
{
    "success": true,
    "user": {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe",
        "user_type": "student",
        "education_level": "high_school",
        "created_at": "2024-01-15T10:30:00"
    }
}
```

#### GET `/api/tutors`
Get list of all tutors.

**Response (Success - 200):**
```json
{
    "success": true,
    "tutors": [
        {
            "id": 2,
            "email": "tutor@example.com",
            "full_name": "Jane Smith",
            "bio": "Expert in Mathematics",
            "education_level": "university"
        }
    ]
}
```

## Frontend Sign-Up Flow

1. User clicks on sign-up link or button
2. Sign-up modal opens with form
3. User fills in:
   - Full Name
   - Email Address
   - Role (Student/Tutor/Parent)
   - Education Level (if Student)
   - Password (min 6 characters)
   - Confirm Password
   - Agree to Terms and Conditions
4. Form is submitted to `/api/signup` endpoint
5. Server validates input and creates user account
6. Success message displayed
7. Modal closes and login modal opens automatically

## Security Features

- **Password Hashing**: Passwords are hashed using SHA256
- **Session Management**: Flask sessions with secure cookies
- **Input Validation**: All user inputs are validated
- **CSRF Protection**: Can be added with Flask-WTF
- **SQL Injection Prevention**: Using parameterized queries with psycopg2

## Files Modified/Created

- ✅ `db_helper.py` - Database connection and helper functions
- ✅ `init_db.py` - Database initialization script
- ✅ `app.py` - Updated with signup/login endpoints
- ✅ `templates/index.html` - Added sign-up modal and JavaScript
- ✅ `requirements.txt` - Added PostgreSQL dependencies

## Troubleshooting

### Connection Error: "could not connect to server"
- Verify database URL is correct
- Check your internet connection
- Verify PostgreSQL server is running

### Error: "relation "users" does not exist"
- Run `python init_db.py` to create tables
- Ensure database initialization completed successfully

### Sign-up fails with "Email already registered"
- Use a different email address
- Or check if account already exists

## Next Steps

1. ✅ Basic authentication system implemented
2. 🔄 (Optional) Add email verification
3. 🔄 (Optional) Add password reset functionality
4. 🔄 (Optional) Add social login (Google, GitHub)
5. 🔄 (Optional) Add two-factor authentication
6. 🔄 (Optional) Implement course management endpoints

## Support

For issues or questions, check:
- Database connection string in `db_helper.py`
- Requirements.txt for dependency versions
- Flask logs for detailed error messages
