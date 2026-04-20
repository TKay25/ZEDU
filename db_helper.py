import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import os
import random
import string
from datetime import datetime

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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_type ON users(user_type);")
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
        cursor.execute("SELECT id, email, full_name, user_type, education_level, country_code, whatsapp_number, avatar_url, bio, created_at FROM users WHERE id = %s;", (user_id,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        print(f"Error getting user: {e}")
        return None
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
    Create a new live session
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO live_sessions (course_id, instructor_id, title, description, scheduled_at, session_url, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'scheduled')
            RETURNING id, title, scheduled_at;
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
                    "scheduled_at": result[2]
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

if __name__ == "__main__":
    # Test database connection and create tables
    print("Connecting to database...")
    if get_db_connection():
        print("✓ Connection successful!")
        print("\nCreating tables...")
        create_tables()
    else:
        print("✗ Connection failed!")
