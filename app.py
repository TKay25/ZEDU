from flask import Flask, render_template, request, jsonify, session, redirect
from db_helper import (create_tables, create_user, authenticate_user, get_user_by_id, get_tutors, get_all_users,
                       init_global_forum, get_global_forum, get_course_forum, get_forum_threads, create_thread,
                       get_thread_posts, create_post)
import os
from datetime import timedelta

app = Flask(__name__)

# Security: Use environment variable for secret key, fallback to dev key
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')
if app.secret_key == 'dev-secret-key-CHANGE-IN-PRODUCTION':
    print("⚠️  WARNING: Using development SECRET_KEY. Set SECRET_KEY environment variable for production!")

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['JSON_SORT_KEYS'] = False

# Initialize database tables on startup
try:
    create_tables()
    init_global_forum()
except Exception as e:
    print(f"⚠️  Warning: Could not initialize database tables: {e}")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    print(f"❌ Internal server error: {error}")
    return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/')
def landing():
    """Render the landing page"""
    return render_template('index_new.html')

@app.route('/api/signup', methods=['POST'])
def signup():
    """
    Handle user sign-up
    Expected JSON: {
        "email": "user@example.com",
        "password": "password123",
        "confirm_password": "password123",
        "full_name": "John Doe",
        "user_type": "student|tutor|parent",
        "education_level": "primary|high_school|university",
        "country_code": "+1",
        "whatsapp_number": "1234567890"
    }
    """
    data = request.get_json()

    # Validation
    if not all([data.get('email'), data.get('password'), data.get('full_name'), data.get('user_type')]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    # Check password confirmation
    if data.get('password') != data.get('confirm_password'):
        return jsonify({"success": False, "message": "Passwords do not match"}), 400

    # Validate password length
    if len(data.get('password', '')) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters"}), 400

    # Validate email format
    if '@' not in data.get('email', ''):
        return jsonify({"success": False, "message": "Invalid email format"}), 400

    # Validate user type
    if data.get('user_type') not in ['student', 'tutor', 'parent']:
        return jsonify({"success": False, "message": "Invalid user type"}), 400

    # Create user (convert email to lowercase for consistency)
    result = create_user(
        email=data.get('email', '').lower(),
        password=data.get('password'),
        full_name=data.get('full_name'),
        user_type=data.get('user_type'),
        education_level=data.get('education_level'),
        country_code=data.get('country_code'),
        whatsapp_number=data.get('whatsapp_number')
    )
    
    print(f"[DEBUG SIGNUP] create_user result: {result}")

    if result['success']:
        print(f"[DEBUG SIGNUP] User created successfully with ID: {result.get('user_id')}")
        return jsonify(result), 201
    else:
        print(f"[DEBUG SIGNUP] User creation failed: {result.get('message')}")
        return jsonify(result), 400

@app.route('/api/login', methods=['POST'])
def login():
    """
    Handle user login
    Expected JSON: {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    data = request.get_json()

    print(data)
    
    # Debug: Print all users in database
    all_users = get_all_users(limit=100)
    print(f"[DEBUG] Total users in database: {len(all_users)}")
    for u in all_users:
        print(f"  - Email: {u['email']}, Type: {u['user_type']}")

    if not data.get('email') or not data.get('password'):
        return jsonify({"success": False, "message": "Email and password required"}), 400

    user = authenticate_user(data.get('email', '').lower(), data.get('password'))
    print(user)
    
    if user:
        session.permanent = True
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['user_type'] = user['user_type']
        
        # Redirect to appropriate dashboard based on user type
        redirect_url = '/'
        if user['user_type'] == 'student':
            redirect_url = '/dashboard'
        elif user['user_type'] == 'tutor':
            redirect_url = '/tutor-dashboard'
        elif user['user_type'] == 'parent':
            redirect_url = '/parent-dashboard'
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user_id": user['id'],
            "email": user['email'],
            "user_type": user['user_type'],
            "redirect_url": redirect_url
        }), 200
    else:
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"}), 200

@app.route('/api/profile', methods=['GET'])
def get_profile():
    """Get current user profile"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    user = get_user_by_id(user_id)
    if user:
        return jsonify({"success": True, "user": dict(user)}), 200
    else:
        return jsonify({"success": False, "message": "User not found"}), 404

@app.route('/api/tutors', methods=['GET'])
def get_tutors_list():
    """Get list of tutors"""
    tutors = get_tutors()
    return jsonify({"success": True, "tutors": [dict(t) for t in tutors]}), 200

@app.route('/api/courses', methods=['GET'])
def get_courses_by_level():
    """Get courses by education level"""
    level = request.args.get('level')
    if not level or level not in ['primary', 'high_school', 'university']:
        return jsonify({"success": False, "message": "Invalid education level"}), 400
    
    try:
        from db_helper import get_courses_by_level as db_get_courses
        courses = db_get_courses(level)
        return jsonify({"success": True, "courses": [dict(c) for c in courses]}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/enrollments', methods=['GET'])
def get_student_enrollments():
    """Get student enrollments"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        from db_helper import get_student_enrollments as db_get_enrollments
        enrollments = db_get_enrollments(user_id)
        return jsonify({"success": True, "enrollments": [dict(e) for e in enrollments]}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/enroll', methods=['POST'])
def enroll_course():
    """Enroll student in a course"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    data = request.get_json()
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({"success": False, "message": "Course ID required"}), 400
    
    try:
        from db_helper import create_enrollment
        result = create_enrollment(user_id, course_id)
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/dashboard')
def student_dashboard():
    """Student dashboard"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')
    
    user = get_user_by_id(user_id)
    if user and user['user_type'] == 'student':
        return render_template('student_dashboard_new.html', user=dict(user))
    return redirect('/')

@app.route('/tutor-dashboard')
def tutor_dashboard():
    """Tutor dashboard"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')
    
    user = get_user_by_id(user_id)
    if user and user['user_type'] == 'tutor':
        return render_template('tutor_dashboard_new.html', user=dict(user))
    return redirect('/')

@app.route('/parent-dashboard')
def parent_dashboard():
    """Parent dashboard"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')
    
    user = get_user_by_id(user_id)
    if user and user['user_type'] == 'parent':
        return render_template('parent_dashboard_new.html', user=dict(user))
    return redirect('/')

@app.route('/api/create-course', methods=['POST'])
def create_course_api():
    """Create a new course (tutor only)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'tutor':
        return jsonify({"success": False, "message": "Only tutors can create courses"}), 403
    
    data = request.get_json()
    required_fields = ['title', 'description', 'category', 'level', 'duration_hours']
    
    if not all(data.get(field) for field in required_fields):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    try:
        from db_helper import create_course
        result = create_course(
            instructor_id=user_id,
            title=data.get('title'),
            description=data.get('description'),
            category=data.get('category'),
            level=data.get('level'),
            duration_hours=int(data.get('duration_hours')),
            price=float(data.get('price', 0.0)),
            image_url=data.get('image_url')
        )
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/my-courses', methods=['GET'])
def get_my_courses():
    """Get courses for logged-in tutor"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        from db_helper import get_instructor_courses
        courses = get_instructor_courses(user_id)
        return jsonify({"success": True, "courses": [dict(c) for c in courses]}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get students for parent dashboard"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        from db_helper import get_students_for_parent
        students = get_students_for_parent(user_id)
        return jsonify({"success": True, "students": [dict(s) for s in students]}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/account')
def account_page():
    """Account page"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')
    
    user = get_user_by_id(user_id)
    if user:
        return render_template('account.html', user=dict(user))
    return redirect('/')

@app.route('/settings')
def settings_page():
    """Settings page"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')
    
    user = get_user_by_id(user_id)
    if user:
        return render_template('settings.html', user=dict(user))
    return redirect('/')

# Forum Routes
@app.route('/forums')
def forums():
    """Forums page"""
    user_id = session.get('user_id')
    return render_template('forums_new.html', user_id=user_id)

@app.route('/forum/thread/<int:thread_id>')
def view_thread(thread_id):
    """View individual thread"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')
    return render_template('thread.html', thread_id=thread_id)

@app.route('/api/forum/global', methods=['GET'])
def get_global_forum_api():
    """Get global forum"""
    try:
        forum = get_global_forum()
        if forum:
            return jsonify({"success": True, "forum": dict(forum)}), 200
        return jsonify({"success": False, "message": "Forum not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/forum/<int:forum_id>/threads', methods=['GET'])
def get_forum_threads_api(forum_id):
    """Get threads in a forum"""
    try:
        threads = get_forum_threads(forum_id)
        return jsonify({"success": True, "threads": [dict(t) for t in threads]}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/forum/<int:forum_id>/thread', methods=['POST'])
def create_thread_api(forum_id):
    """Create new thread in forum"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    data = request.get_json()
    if not data.get('title'):
        return jsonify({"success": False, "message": "Title is required"}), 400
    
    try:
        result = create_thread(forum_id, user_id, data.get('title'))
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/thread/<int:thread_id>/posts', methods=['GET'])
def get_thread_posts_api(thread_id):
    """Get posts in a thread"""
    try:
        posts = get_thread_posts(thread_id)
        return jsonify({"success": True, "posts": [dict(p) for p in posts]}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/thread/<int:thread_id>/post', methods=['POST'])
def create_post_api(thread_id):
    """Create new post in thread"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    data = request.get_json()
    if not data.get('content'):
        return jsonify({"success": False, "message": "Content is required"}), 400
    
    try:
        result = create_post(thread_id, user_id, data.get('content'))
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
