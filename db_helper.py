import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import os
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
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                UNIQUE(student_id, course_id)
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
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(course_id, student_id)
            );
        """)

        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_type ON users(user_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_courses_instructor ON courses(instructor_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);")

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
    Check if a user exists by email
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE email = %s;", (email,))
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
    if user_exists(email):
        return {"success": False, "message": "Email already registered"}

    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}

    cursor = conn.cursor()
    try:
        hashed_password = hash_password(password)
        cursor.execute("""
            INSERT INTO users (email, password, full_name, user_type, education_level, country_code, whatsapp_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (email, hashed_password, full_name, user_type, education_level, country_code, whatsapp_number))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        return {"success": True, "user_id": user_id, "message": "User created successfully"}

    except Exception as e:
        print(f"Error creating user: {e}")
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def get_user_by_email(email):
    """
    Get user by email
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s;", (email,))
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
    user = get_user_by_email(email)
    if not user:
        return None
    
    if verify_password(password, user['password']):
        return user
    return None

def get_user_by_id(user_id):
    """
    Get user by ID
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id, email, full_name, user_type, education_level, created_at FROM users WHERE id = %s;", (user_id,))
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

def get_tutors():
    """
    Get all tutors
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id, email, full_name, bio, education_level FROM users WHERE user_type = 'tutor' LIMIT 100;")
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

if __name__ == "__main__":
    # Test database connection and create tables
    print("Connecting to database...")
    if get_db_connection():
        print("✓ Connection successful!")
        print("\nCreating tables...")
        create_tables()
    else:
        print("✗ Connection failed!")
