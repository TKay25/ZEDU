import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import os
import random
import string
from datetime import datetime
import uuid

# Database connection string
DATABASE_URL = "postgresql://zeduweb_user:qdEe6bfJmlIHAknO2TVbum3SSm2kFvFV@dpg-d7cklfa8qa3s73e9podg-a.oregon-postgres.render.com/zeduweb"

def get_db_connection():
    """
    Get a database connection
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def hash_password(password):
    """
    Hash a password using SHA256
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """
    Verify a password against its hash
    """
    return hash_password(password) == hashed_password

def create_tables():
    """
    Create all necessary database tables
    """
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return False

    cursor = conn.cursor()
    try:
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                user_type VARCHAR(50) NOT NULL CHECK (user_type IN ('student', 'tutor', 'parent')),
                education_level VARCHAR(50) CHECK (education_level IN ('primary', 'high_school', 'university')),
                country_code VARCHAR(5),
                whatsapp_number VARCHAR(20),
                phone VARCHAR(20),
                bio TEXT,
                avatar_url VARCHAR(255),
                verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
        """)

        # Programmers table (System developers/admins)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS programmers (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'developer' CHECK (role IN ('developer', 'system_admin', 'super_admin')),
                status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
        """)

        # Courses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                instructor_id INTEGER NOT NULL,
                category VARCHAR(100),
                level VARCHAR(50) CHECK (level IN ('beginner', 'intermediate', 'advanced')),
                price DECIMAL(10, 2),
                rating DECIMAL(3, 2) DEFAULT 0,
                total_students INTEGER DEFAULT 0,
                duration_hours INTEGER,
                image_url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (instructor_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Enrollments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                progress DECIMAL(3, 2) DEFAULT 0,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                UNIQUE(student_id, course_id),
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            );
        """)

        # Reviews/Ratings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                course_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(course_id, student_id),
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Forums table (global and per-course forums)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forums (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                course_id INTEGER,
                is_global BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            );
        """)

        # Forum Threads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forum_threads (
                id SERIAL PRIMARY KEY,
                forum_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                user_id INTEGER NOT NULL,
                views INTEGER DEFAULT 0,
                last_post_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (forum_id) REFERENCES forums(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Forum Posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forum_posts (
                id SERIAL PRIMARY KEY,
                thread_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                is_solution BOOLEAN DEFAULT FALSE,
                likes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (thread_id) REFERENCES forum_threads(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Course Materials table (PDFs, notes, videos)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_materials (
                id SERIAL PRIMARY KEY,
                course_id INTEGER NOT NULL,
                instructor_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                material_type VARCHAR(50) NOT NULL CHECK (material_type IN ('pdf', 'video', 'document')),
                file_url TEXT NOT NULL,
                file_size INTEGER,
                duration_seconds INTEGER,
                order_index INTEGER DEFAULT 0,
                is_published BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (instructor_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Live Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_sessions (
                id SERIAL PRIMARY KEY,
                course_id INTEGER NOT NULL,
                instructor_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                scheduled_at TIMESTAMP NOT NULL,
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                session_url VARCHAR(500),
                status VARCHAR(50) NOT NULL CHECK (status IN ('scheduled', 'live', 'ended', 'cancelled')),
                is_recorded BOOLEAN DEFAULT FALSE,
                max_participants INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (instructor_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Live Session Participants table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_participants (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                left_at TIMESTAMP,
                duration_minutes INTEGER,
                FOREIGN KEY (session_id) REFERENCES live_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Recorded Lessons table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recorded_lessons (
                id SERIAL PRIMARY KEY,
                course_id INTEGER NOT NULL,
                instructor_id INTEGER NOT NULL,
                session_id INTEGER,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                video_url VARCHAR(500) NOT NULL,
                thumbnail_url VARCHAR(500),
                duration_seconds INTEGER,
                file_size INTEGER,
                views INTEGER DEFAULT 0,
                is_published BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (instructor_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES live_sessions(id) ON DELETE SET NULL
            );
        """)

        # Noticeboards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS noticeboards (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                owner_id INTEGER NOT NULL,
                owner_type VARCHAR(50) NOT NULL CHECK (owner_type IN ('tutor', 'admin')),
                institution_id INTEGER,
                course_id INTEGER,
                is_published BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (institution_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            );
        """)

        # Noticeboard Posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS noticeboard_posts (
                id SERIAL PRIMARY KEY,
                noticeboard_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                priority VARCHAR(50) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
                attachment_url VARCHAR(500),
                views INTEGER DEFAULT 0,
                is_pinned BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (noticeboard_id) REFERENCES noticeboards(id) ON DELETE CASCADE,
                FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Add last_login column to existing users table (for databases upgraded from earlier versions)
        cursor.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
        """)

        # Assignments table (for student dashboard)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id SERIAL PRIMARY KEY,
                course_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                due_date TIMESTAMP NOT NULL,
                priority VARCHAR(50) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
                status VARCHAR(50) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'submitted', 'graded')),
                submission_date TIMESTAMP,
                grade DECIMAL(5, 2),
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Performance Stats table (GPA, study hours, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_stats (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL UNIQUE,
                current_gpa DECIMAL(3, 2) DEFAULT 3.8,
                total_study_hours DECIMAL(10, 2) DEFAULT 0,
                weekly_study_hours DECIMAL(10, 2) DEFAULT 0,
                courses_completed INTEGER DEFAULT 0,
                achievement_points INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Study Resources table (PDFs, videos, articles, notes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_resources (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                resource_type VARCHAR(50) CHECK (resource_type IN ('pdf', 'video', 'article', 'note')),
                content_url VARCHAR(500),
                course_id INTEGER,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
            );
        """)

        # Activity Log table (for Recent Activity section)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                activity_type VARCHAR(100) NOT NULL,
                activity_description TEXT,
                related_entity_type VARCHAR(50),
                related_entity_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Achievements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                achievement_name VARCHAR(255) NOT NULL,
                description TEXT,
                icon_url VARCHAR(500),
                earned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Certificates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                certificate_name VARCHAR(255) NOT NULL,
                issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                certificate_url VARCHAR(500),
                credential_id VARCHAR(100) UNIQUE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            );
        """)

        # Recommended Courses table (personalized recommendations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommended_courses (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                recommendation_score DECIMAL(3, 2),
                reason_for_recommendation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            );
        """)

        # Notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                notification_type VARCHAR(50) NOT NULL CHECK (notification_type IN ('assignment', 'forum', 'message', 'achievement', 'system', 'noticeboard', 'grade', 'announcement')),
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                related_entity_type VARCHAR(50),
                related_entity_id INTEGER,
                read BOOLEAN DEFAULT FALSE,
                read_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Add missing columns to notifications table if they don't exist (migration support)
        try:
            # Add notification_type column if it doesn't exist
            cursor.execute("""
                ALTER TABLE notifications 
                ADD COLUMN IF NOT EXISTS notification_type VARCHAR(50)
            """)
            
            # Set default values for any existing rows
            cursor.execute("""
                UPDATE notifications 
                SET notification_type = 'system' 
                WHERE notification_type IS NULL
            """)
            
            # Add NOT NULL constraint
            cursor.execute("""
                ALTER TABLE notifications 
                ALTER COLUMN notification_type SET NOT NULL
            """)
            
            # Add CHECK constraint
            try:
                cursor.execute("""
                    ALTER TABLE notifications 
                    ADD CONSTRAINT notification_type_check 
                    CHECK (notification_type IN ('assignment', 'forum', 'message', 'achievement', 'system', 'noticeboard', 'grade', 'announcement'))
                """)
            except Exception:
                # Constraint may already exist
                pass
                
        except Exception as e:
            print(f"Note: Migration for notification_type: {e}")
        
        try:
            cursor.execute("""
                ALTER TABLE notifications 
                ADD COLUMN IF NOT EXISTS read BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS read_at TIMESTAMP
            """)
        except Exception as migration_error:
            print(f"Note: Could not add columns to notifications table (may already exist): {migration_error}")

        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_type ON users(user_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_programmers_email ON programmers(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_programmers_status ON programmers(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_courses_instructor ON courses(instructor_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_forums_course ON forums(course_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_forums_global ON forums(is_global);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_threads_forum ON forum_threads(forum_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_threads_user ON forum_threads(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_thread ON forum_posts(thread_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_user ON forum_posts(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_course ON course_materials(course_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_instructor ON course_materials(instructor_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_course ON live_sessions(course_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_instructor ON live_sessions(instructor_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recorded_course ON recorded_lessons(course_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recorded_instructor ON recorded_lessons(instructor_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_noticeboards_owner ON noticeboards(owner_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_noticeboards_institution ON noticeboards(institution_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_noticeboards_course ON noticeboards(course_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_noticeboard ON noticeboard_posts(noticeboard_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_author ON noticeboard_posts(author_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_pinned ON noticeboard_posts(is_pinned);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignments_student ON assignments(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignments_course ON assignments(course_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignments_due ON assignments(due_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_student ON performance_stats(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_student ON study_resources(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_student ON activity_log(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_achievements_student ON achievements(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_certificates_student ON certificates(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommended_student ON recommended_courses(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at);")

        conn.commit()
        print("✓ Database tables created successfully!")
        return True

    except Exception as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def user_exists(email):
    """
    Check if user exists (case-insensitive)
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s);", (email,))
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        print(f"Error checking user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def create_user(email, password, full_name, user_type, education_level=None, country_code=None, whatsapp_number=None):
    """
    Create a new user
    Returns: user_id if successful, None if failed
    """
    print(f"[DEBUG] create_user called: email={email}, full_name={full_name}, user_type={user_type}")
    
    if user_exists(email):
        print(f"[DEBUG] User already exists: {email}")
        return {"success": False, "message": "Email already registered"}

    conn = get_db_connection()
    if not conn:
        print(f"[DEBUG] Database connection failed")
        return {"success": False, "message": "Database connection failed"}

    print(f"[DEBUG] Database connection successful")
    cursor = conn.cursor()
    try:
        hashed_password = hash_password(password)
        print(f"[DEBUG] Password hashed, inserting user...")
        
        cursor.execute("""
            INSERT INTO users (email, password, full_name, user_type, education_level, country_code, whatsapp_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (email, hashed_password, full_name, user_type, education_level, country_code, whatsapp_number))
        
        user_id = cursor.fetchone()[0]
        print(f"[DEBUG] User inserted with ID: {user_id}")
        
        conn.commit()
        print(f"[DEBUG] Transaction committed successfully")
        return {"success": True, "user_id": user_id, "message": "User created successfully"}

    except Exception as e:
        print(f"[ERROR] Error creating user: {e}")
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def get_user_by_email(email):
    """
    Get user by email (case-insensitive)
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(%s);", (email,))
        result = cursor.fetchone()
        return result
    
    except Exception as e:
        print(f"Error getting user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def authenticate_user(email, password):
    """
    Authenticate user by email and password
    Returns: user dict if successful, None if failed
    """
    print(f"[DEBUG] authenticate_user called with email: {email}")
    user = get_user_by_email(email)
    print(f"[DEBUG] get_user_by_email returned: {user}")
    
    if not user:
        print(f"[DEBUG] User not found in database")
        return None
    
    password_match = verify_password(password, user['password'])
    print(f"[DEBUG] Password verification result: {password_match}")
    
    if password_match:
        return user
    print(f"[DEBUG] Password does not match")
    return None

def get_user_by_id(user_id):
    """
    Get user by ID (with all profile fields)
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id, email, full_name, user_type, education_level, country_code, whatsapp_number, avatar_url, bio, created_at, last_login FROM users WHERE id = %s;", (user_id,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        print(f"Error getting user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_last_login(user_id):
    """
    Update the last_login timestamp for a user
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s;", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating last login: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_all_users(limit=100):
    """
    Get all users (limited by default)
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id, email, full_name, user_type, education_level, created_at FROM users LIMIT %s;", (limit,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error getting users: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def update_user_profile(user_id, full_name=None, country_code=None, whatsapp_number=None, bio=None):
    """
    Update user profile information
    Returns: dict with success status
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        # Build dynamic UPDATE query based on provided fields
        updates = []
        values = []
        
        if full_name is not None:
            updates.append("full_name = %s")
            values.append(full_name)
        if country_code is not None:
            updates.append("country_code = %s")
            values.append(country_code)
        if whatsapp_number is not None:
            updates.append("whatsapp_number = %s")
            values.append(whatsapp_number)
        if bio is not None:
            updates.append("bio = %s")
            values.append(bio)
        
        if not updates:
            return {"success": False, "message": "No fields to update"}
        
        # Add updated_at timestamp and user_id
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(user_id)
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s RETURNING id, email, full_name, user_type, education_level, country_code, whatsapp_number, avatar_url, bio, created_at;"
        cursor.execute(query, values)
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            return {"success": True, "message": "Profile updated successfully", "user": dict(result)}
        else:
            return {"success": False, "message": "User not found"}
    except Exception as e:
        print(f"Error updating user profile: {e}")
        conn.rollback()
        return {"success": False, "message": f"Error updating profile: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

def update_user_avatar(user_id, avatar_url):
    """
    Update user avatar URL
    Returns: dict with success status
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET avatar_url = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id, email, full_name, avatar_url;",
            (avatar_url, user_id)
        )
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            return {"success": True, "message": "Avatar updated successfully", "user": dict(result)}
        else:
            return {"success": False, "message": "User not found"}
    except Exception as e:
        print(f"Error updating user avatar: {e}")
        conn.rollback()
        return {"success": False, "message": f"Error updating avatar: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

def get_tutors():
    """
    Get all tutors
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id, email, full_name, bio, education_level, avatar_url FROM users WHERE user_type = 'tutor' LIMIT 100;")
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error getting tutors: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_courses_by_level(education_level):
    """
    Get courses by education level (primary, high_school, university)
    Maps education level to course difficulty levels
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Map education levels to course levels
        level_mapping = {
            'primary': 'beginner',
            'high_school': 'intermediate',
            'university': 'advanced'
        }
        course_level = level_mapping.get(education_level, 'beginner')
        
        cursor.execute("""
            SELECT c.id, c.title, c.description, c.level, c.category, c.duration_hours, 
                   c.rating, c.price, c.total_students, c.image_url, u.full_name as instructor_name, u.id as instructor_id
            FROM courses c
            JOIN users u ON c.instructor_id = u.id
            WHERE c.level = %s
            ORDER BY c.rating DESC, c.total_students DESC
            LIMIT 50;
        """, (course_level,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error getting courses: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_student_enrollments(student_id):
    """
    Get student enrollments with course details
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT e.id, e.progress, e.enrolled_at, c.id as course_id, c.title, c.description,
                   c.level, c.duration_hours, u.full_name as instructor_name
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            JOIN users u ON c.instructor_id = u.id
            WHERE e.student_id = %s;
        """, (student_id,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error getting enrollments: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def create_enrollment(student_id, course_id):
    """
    Create a course enrollment
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO enrollments (student_id, course_id, progress)
            VALUES (%s, %s, 0)
            ON CONFLICT (student_id, course_id) DO UPDATE SET progress = EXCLUDED.progress
            RETURNING id;
        """, (student_id, course_id))
        
        enrollment_id = cursor.fetchone()[0]
        conn.commit()
        return {"success": True, "message": "Enrolled successfully", "enrollment_id": enrollment_id}
    except Exception as e:
        conn.rollback()
        print(f"Error creating enrollment: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

# ==================== PROGRAMMER/DEVELOPER FUNCTIONS ====================

def get_programmer_by_email(email):
    """
    Get programmer by email (case-insensitive)
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM programmers WHERE LOWER(email) = LOWER(%s);", (email,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        print(f"Error getting programmer: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_programmer_by_id(programmer_id):
    """
    Get programmer by ID
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id, email, full_name, role, status, created_at, last_login FROM programmers WHERE id = %s;", (programmer_id,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        print(f"Error getting programmer: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def authenticate_programmer(email, password):
    """
    Authenticate programmer by email and password
    Returns: programmer dict if successful, None if failed
    """
    programmer = get_programmer_by_email(email)
    
    if not programmer:
        return None
    
    # Check if programmer is active
    if programmer.get('status') != 'active':
        return None
    
    password_match = verify_password(password, programmer['password_hash'])
    
    if password_match:
        return programmer
    return None

def update_programmer_last_login(programmer_id):
    """
    Update the last_login timestamp for a programmer
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE programmers SET last_login = CURRENT_TIMESTAMP WHERE id = %s;", (programmer_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating programmer last login: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def create_programmer(email, password, full_name, role='developer'):
    """
    Create a new programmer account (for system initialization)
    Returns: dict with success status and programmer_id
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        # Check if email already exists
        existing = get_programmer_by_email(email)
        if existing:
            return {"success": False, "message": "Email already registered"}
        
        password_hash = hash_password(password)
        
        cursor.execute("""
            INSERT INTO programmers (email, password_hash, full_name, role, status)
            VALUES (%s, %s, %s, %s, 'active')
            RETURNING id
        """, (email, password_hash, full_name, role))
        
        programmer_id = cursor.fetchone()[0]
        conn.commit()
        
        return {
            "success": True, 
            "message": "Programmer account created successfully",
            "programmer_id": programmer_id
        }
    except Exception as e:
        conn.rollback()
        print(f"Error creating programmer: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def get_all_programmers(limit=100):
    """
    Get all active programmers
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id, email, full_name, role, status, created_at, last_login 
            FROM programmers 
            WHERE status = 'active'
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error getting programmers: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def create_course(instructor_id, title, description, category, level, duration_hours, price=0.0, image_url=None):
    """
    Create a new course (for tutors)
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO courses (instructor_id, title, description, category, level, duration_hours, price, image_url, rating, total_students)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 4.5, 0)
            RETURNING id;
        """, (instructor_id, title, description, category, level, duration_hours, price, image_url))
        
        course_id = cursor.fetchone()[0]
        conn.commit()
        return {"success": True, "message": "Course created successfully", "course_id": course_id}
    except Exception as e:
        conn.rollback()
        print(f"Error creating course: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def get_instructor_courses(instructor_id):
    """
    Get all courses created by an instructor
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id, title, description, level, category, duration_hours, price, 
                   rating, total_students, image_url, created_at
            FROM courses
            WHERE instructor_id = %s
            ORDER BY created_at DESC;
        """, (instructor_id,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error getting instructor courses: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def delete_course(course_id, instructor_id):
    """
    Delete a course (cascade deletes all related materials and sessions)
    Verifies the instructor owns the course
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Verify instructor owns this course
        cursor.execute("""
            SELECT instructor_id FROM courses WHERE id = %s
        """, (course_id,))
        course = cursor.fetchone()
        
        if not course:
            return {"success": False, "message": "Course not found"}
        
        if course['instructor_id'] != instructor_id:
            return {"success": False, "message": "Unauthorized: You don't own this course"}
        
        # Delete course (cascade will delete materials, sessions, etc.)
        cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
        conn.commit()
        
        return {"success": True, "message": "Course deleted successfully"}
    except Exception as e:
        conn.rollback()
        print(f"Error deleting course: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def get_students_for_parent(parent_id):
    """
    Get all students linked to a parent (placeholder - returns students)
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id, full_name, email, education_level, created_at
            FROM users
            WHERE user_type = 'student'
            LIMIT 10;
        """)
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error getting students: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def init_global_forum():
    """
    Initialize the global forum on first run
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO forums (name, description, is_global)
            SELECT 'Global Forum', 'Share questions, tips, and discussions with all ZEDU members', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM forums WHERE is_global = TRUE);
        """)
        conn.commit()
        return True
    except Exception as e:
        print(f"Error initializing global forum: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_global_forum():
    """
    Get the global forum
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id, name, description FROM forums WHERE is_global = TRUE LIMIT 1;
        """)
        result = cursor.fetchone()
        return result
    except Exception as e:
        print(f"Error getting global forum: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_course_forum(course_id):
    """
    Get or create forum for a specific course
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id, name, description FROM forums WHERE course_id = %s LIMIT 1;
        """, (course_id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.execute("""
                INSERT INTO forums (name, description, course_id)
                SELECT c.title || ' Forum', 'Discussion forum for ' || c.title, %s
                FROM courses c WHERE c.id = %s
                RETURNING id, name, description;
            """, (course_id, course_id))
            conn.commit()
            result = cursor.fetchone()
        
        return result
    except Exception as e:
        print(f"Error getting course forum: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_all_forums_with_stats():
    """
    Get all forums with thread count, post count, and last activity time
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT 
                f.id,
                f.name,
                f.description,
                f.is_global,
                f.created_at,
                COALESCE(COUNT(DISTINCT ft.id), 0) as thread_count,
                COALESCE(COUNT(DISTINCT fp.id), 0) as post_count,
                COALESCE(COUNT(DISTINCT fp.user_id), 0) as member_count,
                MAX(fp.created_at) as last_activity_time
            FROM forums f
            LEFT JOIN forum_threads ft ON f.id = ft.forum_id
            LEFT JOIN forum_posts fp ON ft.id = fp.thread_id
            GROUP BY f.id, f.name, f.description, f.is_global, f.created_at
            ORDER BY f.is_global DESC, MAX(fp.created_at) DESC NULLS LAST;
        """)
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting forums with stats: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_forum_threads(forum_id, limit=20):
    """
    Get recent threads in a forum with post counts
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT ft.id, ft.title, ft.user_id, u.full_name, u.avatar_url,
                   ft.views, COUNT(fp.id) as reply_count,
                   ft.created_at, ft.last_post_at
            FROM forum_threads ft
            JOIN users u ON ft.user_id = u.id
            LEFT JOIN forum_posts fp ON ft.id = fp.thread_id
            WHERE ft.forum_id = %s
            GROUP BY ft.id, u.id
            ORDER BY ft.last_post_at DESC
            LIMIT %s;
        """, (forum_id, limit))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error getting forum threads: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_thread_info(thread_id):
    """
    Get thread details including title, author, views, reply count
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # First get basic thread info
        cursor.execute("""
            SELECT ft.id, ft.title, ft.user_id, u.full_name, u.user_type,
                   ft.views, ft.created_at
            FROM forum_threads ft
            JOIN users u ON ft.user_id = u.id
            WHERE ft.id = %s
        """, (thread_id,))
        result = cursor.fetchone()
        
        if result:
            # Now get reply count
            cursor.execute("""
                SELECT COUNT(*) as reply_count
                FROM forum_posts
                WHERE thread_id = %s
            """, (thread_id,))
            reply_data = cursor.fetchone()
            if reply_data:
                result['reply_count'] = reply_data['reply_count']
        
        return result
    except Exception as e:
        print(f"Error getting thread info: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()

def create_thread(forum_id, user_id, title):
    """
    Create a new forum thread
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO forum_threads (forum_id, user_id, title)
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (forum_id, user_id, title))
        
        thread_id = cursor.fetchone()[0]
        conn.commit()
        return {"success": True, "message": "Thread created", "thread_id": thread_id}
    except Exception as e:
        conn.rollback()
        print(f"Error creating thread: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def get_thread_posts(thread_id, limit=50):
    """
    Get all posts in a thread with user details
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT fp.id, fp.content, fp.is_solution, fp.likes,
                   u.id as user_id, u.full_name, u.user_type, u.avatar_url,
                   fp.created_at, fp.updated_at
            FROM forum_posts fp
            JOIN users u ON fp.user_id = u.id
            WHERE fp.thread_id = %s
            ORDER BY fp.is_solution DESC, fp.likes DESC, fp.created_at ASC
            LIMIT %s;
        """, (thread_id, limit))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error getting thread posts: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def create_post(thread_id, user_id, content):
    """
    Create a new post in a thread
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO forum_posts (thread_id, user_id, content)
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (thread_id, user_id, content))
        
        post_id = cursor.fetchone()[0]
        
        # Update thread's last_post_at
        cursor.execute("""
            UPDATE forum_threads SET last_post_at = CURRENT_TIMESTAMP WHERE id = %s;
        """, (thread_id,))
        
        conn.commit()
        return {"success": True, "message": "Post created", "post_id": post_id}
    except Exception as e:
        conn.rollback()
        print(f"Error creating post: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

# ============== COURSE MATERIALS ==============

def upload_course_material(course_id, instructor_id, title, description, material_type, file_data, file_size=None, duration_seconds=None):
    """
    Upload course material (PDF, video, document) - stores base64 file data
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO course_materials (course_id, instructor_id, title, description, material_type, file_url, file_size, duration_seconds)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, title, material_type, created_at;
        """, (course_id, instructor_id, title, description, material_type, file_data, file_size, duration_seconds))
        
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            return {
                "success": True,
                "message": f"{material_type.upper()} uploaded successfully",
                "material_id": result[0],
                "material": {
                    "id": result[0],
                    "title": result[1],
                    "type": result[2],
                    "created_at": result[3]
                }
            }
        else:
            return {"success": False, "message": "Failed to upload material"}
    except Exception as e:
        conn.rollback()
        print(f"Error uploading material: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def get_course_materials(course_id):
    """
    Get all materials for a course
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id, title, description, material_type, file_url, file_size, duration_seconds, order_index, created_at
            FROM course_materials
            WHERE course_id = %s AND is_published = TRUE
            ORDER BY order_index, created_at DESC;
        """, (course_id,))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting course materials: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# ============== LIVE SESSIONS ==============

def create_live_session(course_id, instructor_id, title, description, scheduled_at, session_url=None):
    """
    Create a new live session with auto-generated Jitsi room name
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        # Generate unique Jitsi room name if no session_url provided
        if not session_url:
            # Create a unique room name: zedu-<timestamp>-<random>
            room_name = f"zedu-{int(datetime.now().timestamp())}-{uuid.uuid4().hex[:8]}"
            session_url = f"https://meet.jitsi.org/{room_name}"
        
        cursor.execute("""
            INSERT INTO live_sessions (course_id, instructor_id, title, description, scheduled_at, session_url, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'scheduled')
            RETURNING id, title, scheduled_at, session_url;
        """, (course_id, instructor_id, title, description, scheduled_at, session_url))
        
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            return {
                "success": True,
                "message": "Live session created successfully",
                "session_id": result[0],
                "session": {
                    "id": result[0],
                    "title": result[1],
                    "scheduled_at": result[2],
                    "session_url": result[3]
                }
            }
        else:
            return {"success": False, "message": "Failed to create live session"}
    except Exception as e:
        conn.rollback()
        print(f"Error creating live session: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def start_live_session(session_id):
    """
    Start a live session
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE live_sessions
            SET status = 'live', started_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, title, status;
        """, (session_id,))
        
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            return {
                "success": True,
                "message": "Live session started",
                "session": {
                    "id": result[0],
                    "title": result[1],
                    "status": result[2]
                }
            }
        else:
            return {"success": False, "message": "Session not found"}
    except Exception as e:
        conn.rollback()
        print(f"Error starting live session: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def end_live_session(session_id, is_recorded=False):
    """
    End a live session
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE live_sessions
            SET status = 'ended', ended_at = CURRENT_TIMESTAMP, is_recorded = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, title, status;
        """, (is_recorded, session_id))
        
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            return {
                "success": True,
                "message": "Live session ended",
                "session": {
                    "id": result[0],
                    "title": result[1],
                    "status": result[2]
                }
            }
        else:
            return {"success": False, "message": "Session not found"}
    except Exception as e:
        conn.rollback()
        print(f"Error ending live session: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def get_course_live_sessions(course_id, status=None):
    """
    Get live sessions for a course
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if status:
            cursor.execute("""
                SELECT id, title, description, scheduled_at, started_at, ended_at, status, is_recorded
                FROM live_sessions
                WHERE course_id = %s AND status = %s
                ORDER BY scheduled_at DESC;
            """, (course_id, status))
        else:
            cursor.execute("""
                SELECT id, title, description, scheduled_at, started_at, ended_at, status, is_recorded
                FROM live_sessions
                WHERE course_id = %s
                ORDER BY scheduled_at DESC;
            """, (course_id,))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting live sessions: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_live_session(session_id):
    """
    Get details of a specific live session
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT ls.id, ls.course_id, ls.instructor_id, ls.title, ls.description, 
                   ls.scheduled_at, ls.started_at, ls.ended_at, ls.session_url, ls.status, 
                   ls.is_recorded, ls.created_at, ls.updated_at,
                   u.full_name as instructor_name, c.title as course_title
            FROM live_sessions ls
            LEFT JOIN users u ON ls.instructor_id = u.id
            LEFT JOIN courses c ON ls.course_id = c.id
            WHERE ls.id = %s;
        """, (session_id,))
        
        result = cursor.fetchone()
        return dict(result) if result else None
    except Exception as e:
        print(f"Error getting live session: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# ============== RECORDED LESSONS ==============

def save_recorded_lesson(course_id, instructor_id, title, description, video_url, session_id=None, thumbnail_url=None, duration_seconds=None, file_size=None):
    """
    Save a recorded lesson from a live session
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO recorded_lessons (course_id, instructor_id, session_id, title, description, video_url, thumbnail_url, duration_seconds, file_size)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, title, video_url, created_at;
        """, (course_id, instructor_id, session_id, title, description, video_url, thumbnail_url, duration_seconds, file_size))
        
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            return {
                "success": True,
                "message": "Recorded lesson saved successfully",
                "lesson_id": result[0],
                "lesson": {
                    "id": result[0],
                    "title": result[1],
                    "video_url": result[2],
                    "created_at": result[3]
                }
            }
        else:
            return {"success": False, "message": "Failed to save recorded lesson"}
    except Exception as e:
        conn.rollback()
        print(f"Error saving recorded lesson: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def get_recorded_lessons(course_id):
    """
    Get all recorded lessons for a course
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id, title, description, video_url, thumbnail_url, duration_seconds, views, created_at
            FROM recorded_lessons
            WHERE course_id = %s AND is_published = TRUE
            ORDER BY created_at DESC;
        """, (course_id,))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting recorded lessons: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# ============== PARENT-STUDENT LINKING ==============

def generate_verification_code():
    """
    Generate a random 6-digit verification code
    """
    return ''.join(random.choices(string.digits, k=6))

def request_parent_student_link(parent_id, student_email, relationship_type='parent'):
    """
    Create a linking request from parent to student
    Generates a verification code for the student to confirm
    Max 7 links per parent enforced
    Returns: linking_id and verification_code if successful
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        # Verify student exists
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s) AND user_type = 'student'", (student_email,))
        student = cursor.fetchone()
        
        if not student:
            return {"success": False, "message": "Student not found with that email"}
        
        student_id = student[0]
        
        # Check if link already exists with this specific student
        cursor.execute(
            "SELECT id, status FROM parent_student_links WHERE parent_id = %s AND student_id = %s",
            (parent_id, student_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            if existing[1] == 'approved':
                return {"success": False, "message": "This student is already linked to your account"}
            elif existing[1] == 'pending':
                return {"success": False, "message": "A linking request is already pending for this student"}
        
        # Check if parent has reached 7 links limit (count approved links)
        cursor.execute(
            "SELECT COUNT(*) FROM parent_student_links WHERE parent_id = %s AND status = 'approved'",
            (parent_id,)
        )
        approved_count = cursor.fetchone()[0]
        
        if approved_count >= 7:
            return {"success": False, "message": "You can link up to 7 children. Please unlink a child first to add more."}
        
        # Generate verification code
        verification_code = generate_verification_code()
        
        # Create linking request
        cursor.execute("""
            INSERT INTO parent_student_links (parent_id, student_id, relationship_type, status, verification_code, created_at)
            VALUES (%s, %s, %s, 'pending', %s, CURRENT_TIMESTAMP)
            RETURNING id, verification_code, created_at;
        """, (parent_id, student_id, relationship_type, verification_code))
        
        result = cursor.fetchone()
        conn.commit()
        
        return {
            "success": True,
            "message": f"Link request sent to {student_email}",
            "link_id": result[0],
            "verification_code": result[1],
            "created_at": result[2],
            "data": {
                "verification_code": result[1]
            },
            "student_email": student_email
        }
    except Exception as e:
        conn.rollback()
        print(f"Error creating link request: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def approve_parent_student_link(student_id, verification_code):
    """
    Approve a parent-student link using verification code
    Called by student to confirm parent linking
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Find pending link with this code
        cursor.execute("""
            SELECT id, parent_id, student_id, verification_code, status
            FROM parent_student_links
            WHERE student_id = %s AND verification_code = %s AND status = 'pending'
        """, (student_id, verification_code))
        
        link = cursor.fetchone()
        
        if not link:
            return {"success": False, "message": "Invalid verification code or link already processed"}
        
        # Approve the link
        cursor.execute("""
            UPDATE parent_student_links
            SET status = 'approved', approval_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, parent_id, student_id, relationship_type, approval_date;
        """, (link['id'],))
        
        approved_link = cursor.fetchone()
        conn.commit()
        
        # Get parent details for confirmation
        cursor2 = conn.cursor(cursor_factory=RealDictCursor)
        cursor2.execute("SELECT id, full_name, email FROM users WHERE id = %s", (link['parent_id'],))
        parent = cursor2.fetchone()
        cursor2.close()
        
        return {
            "success": True,
            "message": f"Account successfully linked to parent {parent['full_name']}",
            "link": {
                "id": approved_link['id'],
                "parent_id": approved_link['parent_id'],
                "parent_name": parent['full_name'],
                "parent_email": parent['email'],
                "relationship_type": approved_link['relationship_type'],
                "approval_date": approved_link['approval_date']
            }
        }
    except Exception as e:
        conn.rollback()
        print(f"Error approving link: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def reject_parent_student_link(student_id, verification_code):
    """
    Reject a parent-student link
    Called by student to decline parent linking
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        # Find pending link with this code
        cursor.execute("""
            SELECT id, parent_id FROM parent_student_links
            WHERE student_id = %s AND verification_code = %s AND status = 'pending'
        """, (student_id, verification_code))
        
        link = cursor.fetchone()
        
        if not link:
            return {"success": False, "message": "Invalid verification code or link already processed"}
        
        # Reject the link
        cursor.execute("""
            UPDATE parent_student_links
            SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (link[0],))
        
        conn.commit()
        
        return {
            "success": True,
            "message": "Parent linking request rejected"
        }
    except Exception as e:
        conn.rollback()
        print(f"Error rejecting link: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def get_pending_links_for_student(student_id):
    """
    Get all pending parent linking requests for a student
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT psl.id, psl.verification_code, psl.relationship_type, psl.created_at,
                   u.id as parent_id, u.full_name as parent_name, u.email as parent_email, u.education_level
            FROM parent_student_links psl
            JOIN users u ON psl.parent_id = u.id
            WHERE psl.student_id = %s AND psl.status = 'pending'
            ORDER BY psl.created_at DESC;
        """, (student_id,))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting pending links: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_approved_students_for_parent(parent_id):
    """
    Get all approved students linked to a parent
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT psl.id as link_id, psl.relationship_type, psl.approval_date,
                   u.id as student_id, u.full_name as student_name, u.email as student_email, u.education_level, u.created_at
            FROM parent_student_links psl
            JOIN users u ON psl.student_id = u.id
            WHERE psl.parent_id = %s AND psl.status = 'approved'
            ORDER BY u.full_name ASC;
        """, (parent_id,))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting linked students: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_parent_student_links(parent_id):
    """
    Get all student links for a parent (all statuses: pending, approved, rejected)
    Used by parent dashboard to display all access points
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed", "data": []}

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT psl.id as link_id, psl.student_id, psl.status, psl.relationship_type, 
                   psl.verification_code, psl.approval_date, psl.created_at,
                   u.full_name as student_name, u.email as student_email, u.education_level
            FROM parent_student_links psl
            JOIN users u ON psl.student_id = u.id
            WHERE psl.parent_id = %s
            ORDER BY psl.created_at DESC;
        """, (parent_id,))
        
        results = cursor.fetchall()
        links = [dict(row) for row in results]
        
        return {
            "success": True,
            "data": links,
            "count": len(links)
        }
    except Exception as e:
        print(f"Error getting parent student links: {e}")
        return {"success": False, "message": str(e), "data": []}
    finally:
        cursor.close()
        conn.close()

def unlink_parent_student(parent_id, student_id):
    """
    Unlink a parent-student relationship
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Verify the relationship exists and parent owns it
        cursor.execute("""
            SELECT id FROM parent_student_links
            WHERE parent_id = %s AND student_id = %s AND status = 'approved'
        """, (parent_id, student_id))
        
        link = cursor.fetchone()
        if not link:
            return {"success": False, "message": "This student is not linked to your account"}
        
        # Delete the link
        cursor.execute("""
            DELETE FROM parent_student_links
            WHERE parent_id = %s AND student_id = %s
        """, (parent_id, student_id))
        
        conn.commit()
        
        return {"success": True, "message": "Student successfully unlinked"}
    except Exception as e:
        conn.rollback()
        print(f"Error unlinking accounts: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def unlink_parent_student_by_link(parent_id, link_id):
    """
    Unlink a parent-student relationship by link_id
    Works for any status (pending, approved, rejected)
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Verify the link exists and parent owns it
        cursor.execute("""
            SELECT id, status FROM parent_student_links
            WHERE id = %s AND parent_id = %s
        """, (link_id, parent_id))
        
        link = cursor.fetchone()
        if not link:
            return {"success": False, "message": "This link does not exist or you don't have permission to modify it"}
        
        # Delete the link
        cursor.execute("""
            DELETE FROM parent_student_links
            WHERE id = %s
        """, (link_id,))
        
        conn.commit()
        
        status = link['status']
        action = "unlinked" if status == 'approved' else "cancelled"
        return {"success": True, "message": f"Child link successfully {action}"}
    except Exception as e:
        conn.rollback()
        print(f"Error unlinking accounts: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


# ========== ADMINISTRATOR FUNCTIONS ==========

def create_admin_application(email, password, full_name, org_name, org_type, org_phone, org_address, 
                            org_city, org_state, org_zip, payment_plan, estimated_student_count, 
                            country_code=None, whatsapp_number=None):
    """
    Create an administrator application (pending approval)
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Check if email already exists in admin_applications or users table
        cursor.execute("SELECT id FROM admin_applications WHERE LOWER(email) = LOWER(%s)", (email,))
        if cursor.fetchone():
            return {"success": False, "message": "This email is already registered as an administrator"}
        
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
        if cursor.fetchone():
            return {"success": False, "message": "This email is already registered as a user"}
        
        # Hash the password
        password_hash = hash_password(password)
        
        # Insert admin application
        cursor.execute("""
            INSERT INTO admin_applications 
            (full_name, email, password_hash, org_name, org_type, org_phone, org_address, 
             org_city, org_state, org_zip, payment_plan, estimated_student_count, 
             country_code, whatsapp_number, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            RETURNING id
        """, (full_name, email.lower(), password_hash, org_name, org_type, org_phone, 
              org_address, org_city, org_state, org_zip, payment_plan, estimated_student_count, 
              country_code, whatsapp_number))
        
        app_id = cursor.fetchone()['id']
        conn.commit()
        
        return {
            "success": True,
            "message": "Admin application submitted successfully. Awaiting approval.",
            "application_id": app_id
        }
    except Exception as e:
        conn.rollback()
        print(f"Error creating admin application: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_admin_applications(status='all'):
    """
    Get admin applications grouped by status
    status: 'all', 'pending', 'approved', 'rejected'
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        result = {"pending": [], "approved": [], "rejected": []}
        
        statuses_to_fetch = [status] if status != 'all' else ['pending', 'approved', 'rejected']
        
        for st in statuses_to_fetch:
            cursor.execute("""
                SELECT id, full_name, email, org_name, org_type, org_phone, org_address,
                       org_city, org_state, org_zip, payment_plan, estimated_student_count,
                       status, created_at, approved_at, rejection_reason
                FROM admin_applications
                WHERE status = %s
                ORDER BY created_at DESC
            """, (st,))
            
            apps = cursor.fetchall()
            result[st] = [dict(app) for app in apps]
        
        return {"success": True, "data": result}
    except Exception as e:
        print(f"Error fetching admin applications: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def approve_admin_application(application_id, admin_user_id=None):
    """
    Approve an admin application: create user account and move to approved_admins
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Get the application
        cursor.execute("""
            SELECT * FROM admin_applications
            WHERE id = %s AND status = 'pending'
        """, (application_id,))
        
        app = cursor.fetchone()
        if not app:
            return {"success": False, "message": "Application not found or already processed"}
        
        # Create user account for the admin
        cursor.execute("""
            INSERT INTO users 
            (email, password, full_name, user_type, country_code, whatsapp_number)
            VALUES (%s, %s, %s, 'administrator', %s, %s)
            RETURNING id
        """, (app['email'], app['password_hash'], app['full_name'], 
              app['country_code'], app['whatsapp_number']))
        
        user_id = cursor.fetchone()['id']
        
        # Update application status
        cursor.execute("""
            UPDATE admin_applications
            SET status = 'approved', approved_at = CURRENT_TIMESTAMP, approved_by_admin_id = %s
            WHERE id = %s
        """, (admin_user_id, application_id))
        
        # Add to approved_admins table
        cursor.execute("""
            INSERT INTO approved_admins 
            (user_id, application_id, org_name, org_type, org_phone, org_address,
             org_city, org_state, org_zip, payment_plan, estimated_student_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, application_id, app['org_name'], app['org_type'], app['org_phone'],
              app['org_address'], app['org_city'], app['org_state'], app['org_zip'],
              app['payment_plan'], app['estimated_student_count']))
        
        conn.commit()
        
        return {
            "success": True,
            "message": "Admin application approved successfully",
            "user_id": user_id,
            "email": app['email']
        }
    except Exception as e:
        conn.rollback()
        print(f"Error approving admin application: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def reject_admin_application(application_id, reason=""):
    """
    Reject an admin application
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Get the application
        cursor.execute("""
            SELECT email FROM admin_applications
            WHERE id = %s AND status = 'pending'
        """, (application_id,))
        
        app = cursor.fetchone()
        if not app:
            return {"success": False, "message": "Application not found or already processed"}
        
        # Update application status
        cursor.execute("""
            UPDATE admin_applications
            SET status = 'rejected', rejection_reason = %s
            WHERE id = %s
        """, (reason, application_id))
        
        conn.commit()
        
        return {
            "success": True,
            "message": "Admin application rejected",
            "email": app['email']
        }
    except Exception as e:
        conn.rollback()
        print(f"Error rejecting admin application: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def authenticate_admin(email, password):
    """
    Authenticate an administrator (approved admin only)
    Returns user object if successful, None if failed
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Check if email exists in approved_admins (via users table)
        cursor.execute("""
            SELECT u.id, u.email, u.full_name, u.user_type, u.password, u.created_at
            FROM users u
            INNER JOIN approved_admins aa ON u.id = aa.user_id
            WHERE LOWER(u.email) = LOWER(%s) AND u.user_type = 'administrator'
        """, (email,))
        
        user = cursor.fetchone()
        
        if user and verify_password(password, user['password']):
            return dict(user)
        
        return None
    except Exception as e:
        print(f"Error authenticating admin: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


# ========== NOTICEBOARD FUNCTIONS ==========

def create_noticeboard(title, description, owner_id, owner_type, institution_id=None, course_id=None):
    """
    Create a new noticeboard for tutor or admin
    owner_type: 'tutor' or 'admin'
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            INSERT INTO noticeboards (title, description, owner_id, owner_type, institution_id, course_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        """, (title, description, owner_id, owner_type, institution_id, course_id))
        
        result = cursor.fetchone()
        conn.commit()
        
        return {
            "success": True,
            "message": "Noticeboard created successfully",
            "noticeboard_id": result['id']
        }
    except Exception as e:
        conn.rollback()
        print(f"Error creating noticeboard: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_tutor_noticeboards(tutor_id):
    """
    Get all noticeboards owned by a tutor
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id, title, description, course_id, is_published, created_at, updated_at,
                   (SELECT COUNT(*) FROM noticeboard_posts WHERE noticeboard_id = noticeboards.id) as post_count
            FROM noticeboards
            WHERE owner_id = %s AND owner_type = 'tutor'
            ORDER BY is_pinned DESC, created_at DESC
        """, (tutor_id,))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting tutor noticeboards: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_admin_noticeboards(admin_id):
    """
    Get all noticeboards owned by an admin for their institution
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id, title, description, is_published, created_at, updated_at,
                   (SELECT COUNT(*) FROM noticeboard_posts WHERE noticeboard_id = noticeboards.id) as post_count
            FROM noticeboards
            WHERE owner_id = %s AND owner_type = 'admin'
            ORDER BY created_at DESC
        """, (admin_id,))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting admin noticeboards: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_noticeboard_details(noticeboard_id):
    """
    Get detailed information about a noticeboard
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT nb.id, nb.title, nb.description, nb.owner_id, nb.owner_type, nb.is_published,
                   nb.course_id, nb.institution_id, nb.created_at, nb.updated_at,
                   u.full_name as owner_name
            FROM noticeboards nb
            JOIN users u ON nb.owner_id = u.id
            WHERE nb.id = %s
        """, (noticeboard_id,))
        
        result = cursor.fetchone()
        return dict(result) if result else None
    except Exception as e:
        print(f"Error getting noticeboard details: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def create_noticeboard_post(noticeboard_id, author_id, title, content, priority='normal', attachment_url=None):
    """
    Create a post on a noticeboard
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            INSERT INTO noticeboard_posts (noticeboard_id, author_id, title, content, priority, attachment_url)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        """, (noticeboard_id, author_id, title, content, priority, attachment_url))
        
        result = cursor.fetchone()
        conn.commit()
        
        return {
            "success": True,
            "message": "Post created successfully",
            "post_id": result['id']
        }
    except Exception as e:
        conn.rollback()
        print(f"Error creating noticeboard post: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_noticeboard_posts(noticeboard_id, limit=50):
    """
    Get all posts from a noticeboard, pinned posts first
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT np.id, np.title, np.content, np.priority, np.attachment_url, np.views,
                   np.is_pinned, np.created_at, np.updated_at,
                   u.id as author_id, u.full_name as author_name, u.avatar_url
            FROM noticeboard_posts np
            JOIN users u ON np.author_id = u.id
            WHERE np.noticeboard_id = %s
            ORDER BY np.is_pinned DESC, np.created_at DESC
            LIMIT %s
        """, (noticeboard_id, limit))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting noticeboard posts: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def update_post_views(post_id):
    """
    Increment view count for a post
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE noticeboard_posts
            SET views = views + 1
            WHERE id = %s
        """, (post_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating post views: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def pin_noticeboard_post(post_id, noticeboard_id):
    """
    Pin a post to the top of a noticeboard
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE noticeboard_posts
            SET is_pinned = TRUE
            WHERE id = %s AND noticeboard_id = %s
        """, (post_id, noticeboard_id))
        
        conn.commit()
        return {"success": True, "message": "Post pinned successfully"}
    except Exception as e:
        conn.rollback()
        print(f"Error pinning post: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def unpin_noticeboard_post(post_id, noticeboard_id):
    """
    Unpin a post from the top of a noticeboard
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE noticeboard_posts
            SET is_pinned = FALSE
            WHERE id = %s AND noticeboard_id = %s
        """, (post_id, noticeboard_id))
        
        conn.commit()
        return {"success": True, "message": "Post unpinned successfully"}
    except Exception as e:
        conn.rollback()
        print(f"Error unpinning post: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def delete_noticeboard_post(post_id, noticeboard_id):
    """
    Delete a post from a noticeboard
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM noticeboard_posts
            WHERE id = %s AND noticeboard_id = %s
        """, (post_id, noticeboard_id))
        
        conn.commit()
        return {"success": True, "message": "Post deleted successfully"}
    except Exception as e:
        conn.rollback()
        print(f"Error deleting post: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_student_noticeboards(student_id):
    """
    Get all noticeboards a student has access to:
    1. From tutors of courses they're enrolled in
    2. From admin institutions if they belong to any
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Get noticeboards from tutors of enrolled courses
        cursor.execute("""
            SELECT DISTINCT nb.id, nb.title, nb.description, nb.owner_id, nb.owner_type,
                   u.full_name as owner_name, c.id as course_id, c.title as course_title,
                   nb.created_at, nb.updated_at
            FROM noticeboard_posts np
            JOIN noticeboards nb ON np.noticeboard_id = nb.id
            JOIN users u ON nb.owner_id = u.id
            LEFT JOIN courses c ON nb.course_id = c.id
            LEFT JOIN enrollments e ON c.id = e.course_id AND e.student_id = %s
            WHERE (e.student_id = %s OR nb.course_id IS NULL) AND nb.is_published = TRUE
            ORDER BY nb.created_at DESC
        """, (student_id, student_id))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting student noticeboards: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ========== NOTIFICATION FUNCTIONS ==========

def create_notification(user_id, notification_type, title, message, related_entity_type=None, related_entity_id=None):
    """
    Create a notification for a user
    notification_type: assignment, forum, message, achievement, system, noticeboard, grade, announcement
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO notifications 
            (user_id, notification_type, title, message, related_entity_type, related_entity_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, notification_type, title, message, related_entity_type, related_entity_id))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error creating notification: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_user_notifications(user_id, limit=20, unread_only=False):
    """
    Get notifications for a user
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            SELECT id, user_id, notification_type, title, message, 
                   related_entity_type, related_entity_id, read, read_at, created_at, expires_at
            FROM notifications
            WHERE user_id = %s
        """
        params = [user_id]
        
        if unread_only:
            query += " AND read = FALSE"
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting notifications: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_unread_notification_count(user_id):
    """
    Get count of unread notifications for a user
    """
    conn = get_db_connection()
    if not conn:
        return 0

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM notifications
            WHERE user_id = %s AND read = FALSE
        """, (user_id,))
        
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"Error getting unread notification count: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()


def mark_notification_as_read(notification_id):
    """
    Mark a notification as read
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE notifications
            SET read = TRUE, read_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (notification_id,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error marking notification as read: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def mark_all_notifications_as_read(user_id):
    """
    Mark all unread notifications as read for a user
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE notifications
            SET read = TRUE, read_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND read = FALSE
        """, (user_id,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error marking all notifications as read: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def delete_notification(notification_id):
    """
    Delete a notification
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error deleting notification: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# ============== FORUM TAGS ==============

def get_popular_tags(limit=8):
    """
    Extract and count popular tags from forum thread titles
    Returns top tags by frequency
    """
    import re
    
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        # Get all forum thread titles
        cursor.execute("""
            SELECT title FROM forum_threads
            ORDER BY created_at DESC
        """)
        
        threads = cursor.fetchall()
        
        # Extract tags from titles (look for #hashtag pattern)
        tag_count = {}
        for thread in threads:
            title = thread[0] if thread[0] else ""
            # Find all hashtags in the title
            tags = re.findall(r'#(\w+)', title)
            for tag in tags:
                tag_lower = tag.lower()
                tag_count[tag_lower] = tag_count.get(tag_lower, 0) + 1
        
        # Sort by count and get top tags
        popular_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # If no tags found in titles, return default popular tags
        if not popular_tags:
            default_tags = ['python', 'javascript', 'databases', 'web-development', 'project-help', 'study-tips', 'career', 'networking']
            return [{'tag': tag, 'count': 0} for tag in default_tags[:limit]]
        
        return [{'tag': tag, 'count': count} for tag, count in popular_tags]
    except Exception as e:
        print(f"Error getting popular tags: {e}")
        # Return default tags on error
        default_tags = ['python', 'javascript', 'databases', 'web-development', 'project-help', 'study-tips', 'career', 'networking']
        return [{'tag': tag, 'count': 0} for tag in default_tags[:limit]]
    finally:
        cursor.close()
        conn.close()


# ============== STUDENT DASHBOARD DATA ==============

def get_student_gpa(student_id):
    """
    Get student's GPA (calculated from course reviews/ratings)
    """
    conn = get_db_connection()
    if not conn:
        return 0.0

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT AVG(rating * 1.0) FROM reviews
            WHERE student_id = %s
        """, (student_id,))
        
        result = cursor.fetchone()
        gpa = result[0] if result[0] else 0.0
        return round(gpa, 2)
    except Exception as e:
        print(f"Error getting student GPA: {e}")
        return 0.0
    finally:
        cursor.close()
        conn.close()


def get_student_study_hours(student_id, days=7):
    """
    Get total study hours for the last N days
    """
    conn = get_db_connection()
    if not conn:
        return 0

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT SUM(EXTRACT(EPOCH FROM (ended_at - started_at)) / 3600)
            FROM live_sessions
            WHERE instructor_id = %s AND status = 'ended' AND ended_at > NOW() - INTERVAL '%s days'
        """, (student_id, days))
        
        result = cursor.fetchone()
        hours = int(result[0]) if result[0] else 0
        return hours
    except Exception as e:
        print(f"Error getting study hours: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()


def get_student_recommended_courses(student_id, limit=3):
    """
    Get recommended courses based on student's education level
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Get student's education level
        cursor.execute("SELECT education_level FROM users WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        education_level = student['education_level'] if student else 'university'
        
        # Get courses not yet enrolled in
        cursor.execute("""
            SELECT c.id, c.title, u.full_name as instructor_name, c.level, c.total_students
            FROM courses c
            JOIN users u ON c.instructor_id = u.id
            WHERE c.level = %s 
            AND c.id NOT IN (SELECT course_id FROM enrollments WHERE student_id = %s)
            ORDER BY c.rating DESC, c.total_students DESC
            LIMIT %s
        """, (education_level, student_id, limit))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting recommended courses: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_student_activity(student_id, limit=10):
    """
    Get recent activity for a student
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Get various activities from different tables
        cursor.execute("""
            SELECT 
                'assignment' as activity_type,
                'Assignment Submitted' as title,
                c.title as course_name,
                fp.content as description,
                fp.created_at
            FROM forum_posts fp
            JOIN forum_threads ft ON fp.thread_id = ft.id
            JOIN forums f ON ft.forum_id = f.id
            JOIN courses c ON f.course_id = c.id
            WHERE fp.user_id = %s
            UNION ALL
            SELECT 
                'enrollment' as activity_type,
                'Course Enrolled' as title,
                c.title as course_name,
                'Enrolled in ' || c.title as description,
                e.enrolled_at as created_at
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE e.student_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (student_id, student_id, limit))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting student activity: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Test database connection and create tables
    print("Connecting to database...")
    if get_db_connection():
        print("✓ Connection successful!")
        print("\nCreating tables...")
        create_tables()
    else:
        print("✗ Connection failed!")
