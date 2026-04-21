from flask import Flask, render_template, request, jsonify, session, redirect
from db_helper import (create_tables, create_user, authenticate_user, get_user_by_id, get_tutors, get_all_users,
                       init_global_forum, get_global_forum, get_course_forum, get_forum_threads, create_thread,
                       get_thread_posts, create_post, update_user_profile, update_user_avatar,
                       upload_course_material, get_course_materials, create_live_session, start_live_session,
                       end_live_session, get_course_live_sessions, save_recorded_lesson, get_recorded_lessons,
                       request_parent_student_link, approve_parent_student_link, reject_parent_student_link,
                       get_pending_links_for_student, get_approved_students_for_parent, unlink_parent_student,
                       get_parent_student_links, unlink_parent_student_by_link, create_admin_application,
                       get_admin_applications, approve_admin_application, reject_admin_application, authenticate_admin,
                       create_noticeboard, get_tutor_noticeboards, get_admin_noticeboards, get_noticeboard_details,
                       create_noticeboard_post, get_noticeboard_posts, update_post_views, pin_noticeboard_post,
                       unpin_noticeboard_post, delete_noticeboard_post, get_student_noticeboards, update_last_login,
                       get_all_forums_with_stats, create_notification, get_user_notifications, 
                       get_unread_notification_count, mark_notification_as_read, mark_all_notifications_as_read, 
                       delete_notification, get_popular_tags, get_student_gpa, get_student_study_hours,
                       get_student_recommended_courses, get_student_activity, authenticate_programmer,
                       get_programmer_by_id, update_programmer_last_login, create_programmer, get_all_programmers)
import os
from datetime import timedelta
import base64

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

@app.route('/noticeboards')
def noticeboards():
    """Render the noticeboards page"""
    if 'user_id' not in session:
        return redirect('/')
    return render_template('noticeboards.html')

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
        "education_level": "primary|high_school|university" (NOT required for parents),
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
    if data.get('user_type') not in ['student', 'tutor', 'parent', 'administrator']:
        return jsonify({"success": False, "message": "Invalid user type"}), 400

    # Education level is optional for parents and administrators
    education_level = data.get('education_level')
    if data.get('user_type') not in ['parent', 'administrator'] and not education_level:
        return jsonify({"success": False, "message": "Education level required for students and tutors"}), 400

    # Handle administrator signup
    if data.get('user_type') == 'administrator':
        # Validate admin-specific fields
        required_admin_fields = ['org_name', 'org_type', 'org_phone', 'org_address', 
                                'org_city', 'org_state', 'org_zip', 'payment_plan', 'estimated_student_count']
        
        for field in required_admin_fields:
            if not data.get(field):
                return jsonify({"success": False, "message": f"Missing required field: {field}"}), 400
        
        # Create admin application (pending approval)
        result = create_admin_application(
            email=data.get('email', '').lower(),
            password=data.get('password'),
            full_name=data.get('full_name'),
            org_name=data.get('org_name'),
            org_type=data.get('org_type'),
            org_phone=data.get('org_phone'),
            org_address=data.get('org_address'),
            org_city=data.get('org_city'),
            org_state=data.get('org_state'),
            org_zip=data.get('org_zip'),
            payment_plan=data.get('payment_plan'),
            estimated_student_count=int(data.get('estimated_student_count')),
            country_code=data.get('country_code'),
            whatsapp_number=data.get('whatsapp_number')
        )
        
        print(f"[DEBUG SIGNUP ADMIN] create_admin_application result: {result}")
        
        if result['success']:
            print(f"[DEBUG SIGNUP ADMIN] Admin application created successfully with ID: {result.get('application_id')}")
            return jsonify(result), 201
        else:
            print(f"[DEBUG SIGNUP ADMIN] Admin application creation failed: {result.get('message')}")
            return jsonify(result), 400
    
    # Regular user signup (student, tutor, parent)
    result = create_user(
        email=data.get('email', '').lower(),
        password=data.get('password'),
        full_name=data.get('full_name'),
        user_type=data.get('user_type'),
        education_level=education_level,  # Optional for parents
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
        
        # Update last login timestamp (non-blocking - doesn't affect login if it fails)
        try:
            update_last_login(user['id'])
        except Exception as e:
            print(f"Warning: Could not update last login: {e}")
        
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

@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    """Update user profile information"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    data = request.get_json()
    
    # Update profile with provided fields
    result = update_user_profile(
        user_id=user_id,
        full_name=data.get('full_name'),
        country_code=data.get('country'),
        whatsapp_number=data.get('whatsapp'),
        bio=data.get('bio')
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@app.route('/api/profile/upload-photo', methods=['POST'])
def upload_profile_photo():
    """Upload and update user profile photo"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    try:
        data = request.get_json()
        photo_data = data.get('photo')
        
        if not photo_data:
            return jsonify({"success": False, "message": "No photo provided"}), 400
        
        # Store the base64 encoded photo data directly
        # In production, you might want to save to cloud storage (AWS S3, etc.)
        # For now, we store it as a data URL
        result = update_user_avatar(user_id, photo_data)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        print(f"Error uploading photo: {e}")
        return jsonify({"success": False, "message": f"Error uploading photo: {str(e)}"}), 500

@app.route('/api/user-profile', methods=['GET'])
def get_user_profile():
    """Get user profile info (name, education level, initials)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    user = get_user_by_id(user_id)
    if user:
        name = user.get('full_name') or user.get('name') or user.get('email', '').split('@')[0]
        education_level = user.get('education_level') or 'Not Specified'
        # Generate initials from name
        initials = ''.join([word[0].upper() for word in name.split() if word])[:2]
        
        return jsonify({
            "success": True,
            "profile": {
                "name": name,
                "education_level": education_level,
                "initials": initials or "ZV"
            }
        }), 200
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

@app.route('/api/student/stats', methods=['GET'])
def get_student_stats():
    """Get student dashboard statistics (GPA, study hours, etc)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        gpa = get_student_gpa(user_id)
        study_hours = get_student_study_hours(user_id, days=7)
        
        return jsonify({
            "success": True,
            "stats": {
                "gpa": gpa,
                "study_hours": study_hours
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/student/recommended-courses', methods=['GET'])
def get_recommended_courses():
    """Get recommended courses for student"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        limit = request.args.get('limit', 3, type=int)
        courses = get_student_recommended_courses(user_id, limit)
        return jsonify({"success": True, "courses": [dict(c) for c in courses]}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/student/activity', methods=['GET'])
def get_activity():
    """Get recent activity for student"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        limit = request.args.get('limit', 10, type=int)
        activity = get_student_activity(user_id, limit)
        return jsonify({"success": True, "activity": [dict(a) for a in activity]}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """Universal dashboard that redirects to appropriate user dashboard"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')
    
    user = get_user_by_id(user_id)
    if not user:
        return redirect('/')
    
    # Redirect to appropriate dashboard based on user type
    if user['user_type'] == 'student':
        return render_template('student_dashboard_new.html', user=dict(user))
    elif user['user_type'] == 'tutor':
        return render_template('tutor_dashboard_new.html', user=dict(user))
    elif user['user_type'] == 'parent':
        return render_template('parent_dashboard_new.html', user=dict(user))
    
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

@app.route('/api/course/<int:course_id>', methods=['DELETE'])
def delete_course_api(course_id):
    """Delete a course (tutor only)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'tutor':
        return jsonify({"success": False, "message": "Only tutors can delete courses"}), 403
    
    try:
        from db_helper import delete_course
        result = delete_course(course_id, user_id)
        return jsonify(result), 200 if result['success'] else 400
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

@app.route('/api/forums', methods=['GET'])
def get_forums_api():
    """Get all forums with statistics"""
    try:
        forums = get_all_forums_with_stats()
        if forums:
            return jsonify({"success": True, "forums": forums}), 200
        return jsonify({"success": True, "forums": []}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/forums/popular-tags', methods=['GET'])
def get_popular_tags_api():
    """Get popular tags from forum discussions"""
    try:
        limit = request.args.get('limit', 8, type=int)
        if limit < 1 or limit > 50:
            limit = 8
        tags = get_popular_tags(limit)
        return jsonify({"success": True, "tags": tags}), 200
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

# ============== COURSE MATERIALS ROUTES ==============

@app.route('/api/course/<int:course_id>/materials', methods=['GET'])
def get_course_materials_api(course_id):
    """Get all course materials"""
    try:
        materials = get_course_materials(course_id)
        return jsonify({"success": True, "materials": materials}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/course/<int:course_id>/material/upload', methods=['POST'])
def upload_material_api(course_id):
    """Upload course material (PDF, video, etc.) - accepts base64 encoded file data"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'tutor':
        return jsonify({"success": False, "message": "Only tutors can upload materials"}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not all([data.get('title'), data.get('material_type'), data.get('file_data')]):
        return jsonify({"success": False, "message": "Missing required fields (title, material_type, file_data)"}), 400
    
    # Validate material type
    if data.get('material_type') not in ['pdf', 'video', 'document']:
        return jsonify({"success": False, "message": "Invalid material type"}), 400
    
    try:
        result = upload_course_material(
            course_id=course_id,
            instructor_id=user_id,
            title=data.get('title'),
            description=data.get('description'),
            material_type=data.get('material_type'),
            file_data=data.get('file_data'),
            file_size=data.get('file_size'),
            duration_seconds=data.get('duration_seconds')
        )
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ============== LIVE SESSIONS ROUTES ==============

@app.route('/api/course/<int:course_id>/sessions', methods=['GET'])
def get_sessions_api(course_id):
    """Get all live sessions for a course"""
    try:
        status = request.args.get('status')  # Optional: filter by status (scheduled, live, ended)
        sessions = get_course_live_sessions(course_id, status)
        return jsonify({"success": True, "sessions": sessions}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/course/<int:course_id>/session/create', methods=['POST'])
def create_session_api(course_id):
    """Create a new live session"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'tutor':
        return jsonify({"success": False, "message": "Only tutors can create live sessions"}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not all([data.get('title'), data.get('scheduled_at')]):
        return jsonify({"success": False, "message": "Missing required fields (title, scheduled_at)"}), 400
    
    try:
        result = create_live_session(
            course_id=course_id,
            instructor_id=user_id,
            title=data.get('title'),
            description=data.get('description'),
            scheduled_at=data.get('scheduled_at'),
            session_url=data.get('session_url')
        )
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/session/<int:session_id>/start', methods=['POST'])
def start_session_api(session_id):
    """Start a live session"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        result = start_live_session(session_id)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/session/<int:session_id>/end', methods=['POST'])
def end_session_api(session_id):
    """End a live session"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    data = request.get_json() or {}
    is_recorded = data.get('is_recorded', False)
    
    try:
        result = end_live_session(session_id, is_recorded)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ============== RECORDED LESSONS ROUTES ==============

@app.route('/api/course/<int:course_id>/lessons', methods=['GET'])
def get_lessons_api(course_id):
    """Get all recorded lessons for a course"""
    try:
        lessons = get_recorded_lessons(course_id)
        return jsonify({"success": True, "lessons": lessons}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/course/<int:course_id>/lesson/save', methods=['POST'])
def save_lesson_api(course_id):
    """Save a recorded lesson from a live session"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'tutor':
        return jsonify({"success": False, "message": "Only tutors can save recorded lessons"}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not all([data.get('title'), data.get('video_url')]):
        return jsonify({"success": False, "message": "Missing required fields (title, video_url)"}), 400
    
    try:
        result = save_recorded_lesson(
            course_id=course_id,
            instructor_id=user_id,
            title=data.get('title'),
            description=data.get('description'),
            video_url=data.get('video_url'),
            session_id=data.get('session_id'),
            thumbnail_url=data.get('thumbnail_url'),
            duration_seconds=data.get('duration_seconds'),
            file_size=data.get('file_size')
        )
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ============== PARENT-STUDENT LINKING ROUTES ==============

@app.route('/api/parent/link-student', methods=['POST'])
def request_link_student():
    """Parent requests to link a student account"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'parent':
        return jsonify({"success": False, "message": "Only parents can link students"}), 403
    
    data = request.get_json()
    student_email = data.get('student_email')
    relationship_type = data.get('relationship_type', 'parent')
    
    if not student_email:
        return jsonify({"success": False, "message": "Student email is required"}), 400
    
    if relationship_type not in ['parent', 'guardian', 'custodian']:
        return jsonify({"success": False, "message": "Invalid relationship type"}), 400
    
    try:
        result = request_parent_student_link(user_id, student_email, relationship_type)
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/student/pending-links', methods=['GET'])
def get_pending_links():
    """Get pending parent linking requests for a student"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'student':
        return jsonify({"success": False, "message": "Only students can view pending links"}), 403
    
    try:
        links = get_pending_links_for_student(user_id)
        return jsonify({"success": True, "pending_links": links}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/student/approve-link/<verification_code>', methods=['POST'])
def approve_link(verification_code):
    """Student approves a parent linking request"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'student':
        return jsonify({"success": False, "message": "Only students can approve links"}), 403
    
    try:
        result = approve_parent_student_link(user_id, verification_code)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/student/reject-link/<verification_code>', methods=['POST'])
def reject_link(verification_code):
    """Student rejects a parent linking request"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'student':
        return jsonify({"success": False, "message": "Only students can reject links"}), 403
    
    try:
        result = reject_parent_student_link(user_id, verification_code)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/parent/linked-students', methods=['GET'])
def get_linked_students():
    """Get all students linked to a parent (all statuses: pending, approved, rejected)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'parent':
        return jsonify({"success": False, "message": "Only parents can view linked students"}), 403
    
    try:
        result = get_parent_student_links(user_id)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/parent/unlink-student', methods=['POST'])
def unlink_student_endpoint():
    """Parent unlinks a student account by link_id"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'parent':
        return jsonify({"success": False, "message": "Only parents can unlink students"}), 403
    
    try:
        data = request.get_json()
        link_id = data.get('link_id')
        
        if not link_id:
            return jsonify({"success": False, "message": "link_id is required"}), 400
        
        result = unlink_parent_student_by_link(user_id, link_id)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ========== ADMINISTRATOR ENDPOINTS ==========

@app.route('/admin-approvals')
def admin_approvals_page():
    """Render the admin approvals dashboard"""
    # This page should only be accessible after admin login
    user_id = session.get('user_id')
    user = get_user_by_id(user_id) if user_id else None
    
    if not user or user['user_type'] != 'administrator':
        return redirect('/')
    
    return render_template('admin_approvals.html')

@app.route('/api/admin-login', methods=['POST'])
def admin_login():
    """
    Handle administrator login
    Expected JSON: {
        "email": "admin@example.com",
        "password": "password123"
    }
    """
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({"success": False, "message": "Email and password required"}), 400
    
    admin = authenticate_admin(data.get('email', '').lower(), data.get('password'))
    
    if admin:
        session.permanent = True
        session['user_id'] = admin['id']
        session['email'] = admin['email']
        session['user_type'] = admin['user_type']
        
        # Update last login timestamp (non-blocking - doesn't affect login if it fails)
        try:
            update_last_login(admin['id'])
        except Exception as e:
            print(f"Warning: Could not update last login: {e}")
        
        return jsonify({
            "success": True,
            "message": "Admin login successful",
            "user_id": admin['id'],
            "email": admin['email'],
            "user_type": admin['user_type'],
            "redirect_url": "/admin-approvals"
        }), 200
    else:
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

@app.route('/api/admin/applications', methods=['GET'])
def get_admin_applications_endpoint():
    """Get all admin applications grouped by status"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'administrator':
        return jsonify({"success": False, "message": "Unauthorized access"}), 403
    
    try:
        result = get_admin_applications()
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/applications/approve', methods=['POST'])
def approve_admin_application_endpoint():
    """Approve an admin application"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'administrator':
        return jsonify({"success": False, "message": "Unauthorized access"}), 403
    
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        
        if not admin_id:
            return jsonify({"success": False, "message": "admin_id is required"}), 400
        
        result = approve_admin_application(admin_id, user_id)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/applications/reject', methods=['POST'])
def reject_admin_application_endpoint():
    """Reject an admin application"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user = get_user_by_id(user_id)
    if not user or user['user_type'] != 'administrator':
        return jsonify({"success": False, "message": "Unauthorized access"}), 403
    
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        reason = data.get('reason', '')
        
        if not admin_id:
            return jsonify({"success": False, "message": "admin_id is required"}), 400
        
        result = reject_admin_application(admin_id, reason)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ========== PROGRAMMER/DEVELOPER ENDPOINTS ==========

@app.route('/api/programmer-login', methods=['POST'])
def programmer_login():
    """
    Handle programmer/developer login
    Expected JSON: {
        "email": "developer@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Email and password are required"
            }), 400
        
        programmer = authenticate_programmer(email, password)
        
        if not programmer:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401
        
        # Update last login
        update_programmer_last_login(programmer['id'])
        
        # Store in session
        session['programmer_id'] = programmer['id']
        session['programmer_type'] = 'programmer'
        session.modified = True
        
        return jsonify({
            "success": True,
            "message": "Programmer login successful",
            "redirect_url": "/admin-approvals",
            "programmer": {
                "id": programmer['id'],
                "email": programmer['email'],
                "full_name": programmer['full_name'],
                "role": programmer['role']
            }
        }), 200
    
    except Exception as e:
        print(f"Programmer login error: {e}")
        return jsonify({
            "success": False,
            "message": "Login failed"
        }), 500

@app.route('/programmer-approvals')
def programmer_approvals_page():
    """Render the programmer approvals dashboard"""
    programmer_id = session.get('programmer_id')
    programmer = get_programmer_by_id(programmer_id) if programmer_id else None
    
    if not programmer:
        return redirect('/')
    
    return render_template('admin_approvals.html', user_type='programmer')

@app.route('/api/programmer/profile', methods=['GET'])
def get_programmer_profile():
    """Get current programmer profile"""
    programmer_id = session.get('programmer_id')
    if not programmer_id:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    programmer = get_programmer_by_id(programmer_id)
    if not programmer:
        return jsonify({"success": False, "message": "Programmer not found"}), 404
    
    return jsonify({
        "success": True,
        "programmer": programmer
    }), 200

# ========== NOTICEBOARD ROUTES ==========

@app.route('/api/noticeboards/create', methods=['POST'])
def api_create_noticeboard():
    """Create a new noticeboard (tutor or admin only)"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    if not user or user['user_type'] not in ['tutor', 'administrator']:
        return jsonify({"success": False, "message": "Only tutors and admins can create noticeboards"}), 403
    
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description', '')
        course_id = data.get('course_id') if user['user_type'] == 'tutor' else None
        
        if not title:
            return jsonify({"success": False, "message": "Title is required"}), 400
        
        result = create_noticeboard(
            title=title,
            description=description,
            owner_id=user_id,
            owner_type=user['user_type'],
            institution_id=user_id if user['user_type'] == 'administrator' else None,
            course_id=course_id
        )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/noticeboards/tutor/<int:tutor_id>', methods=['GET'])
def api_get_tutor_noticeboards(tutor_id):
    """Get all noticeboards for a tutor"""
    try:
        noticeboards = get_tutor_noticeboards(tutor_id)
        return jsonify({"success": True, "noticeboards": noticeboards}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/noticeboards/admin/<int:admin_id>', methods=['GET'])
def api_get_admin_noticeboards(admin_id):
    """Get all noticeboards for an admin"""
    try:
        noticeboards = get_admin_noticeboards(admin_id)
        return jsonify({"success": True, "noticeboards": noticeboards}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/noticeboards/student/my-noticeboards', methods=['GET'])
def api_get_my_noticeboards():
    """Get all noticeboards accessible to the logged-in student"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    if not user or user['user_type'] != 'student':
        return jsonify({"success": False, "message": "Only students can access this endpoint"}), 403
    
    try:
        noticeboards = get_student_noticeboards(user_id)
        return jsonify({"success": True, "noticeboards": noticeboards}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/noticeboards/<int:noticeboard_id>', methods=['GET'])
def api_get_noticeboard(noticeboard_id):
    """Get noticeboard details and posts"""
    try:
        noticeboard = get_noticeboard_details(noticeboard_id)
        
        if not noticeboard:
            return jsonify({"success": False, "message": "Noticeboard not found"}), 404
        
        posts = get_noticeboard_posts(noticeboard_id)
        
        return jsonify({
            "success": True,
            "noticeboard": noticeboard,
            "posts": posts
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/noticeboards/<int:noticeboard_id>/post', methods=['POST'])
def api_create_noticeboard_post(noticeboard_id):
    """Create a post on a noticeboard"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    try:
        # Verify user can post
        noticeboard = get_noticeboard_details(noticeboard_id)
        
        if not noticeboard:
            return jsonify({"success": False, "message": "Noticeboard not found"}), 404
        
        # Only owner or admins/tutors of the institution can post
        if user['user_type'] not in ['tutor', 'administrator'] and noticeboard['owner_id'] != user_id:
            return jsonify({"success": False, "message": "You don't have permission to post here"}), 403
        
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        priority = data.get('priority', 'normal')
        attachment_url = data.get('attachment_url')
        
        if not title or not content:
            return jsonify({"success": False, "message": "Title and content are required"}), 400
        
        result = create_noticeboard_post(
            noticeboard_id=noticeboard_id,
            author_id=user_id,
            title=title,
            content=content,
            priority=priority,
            attachment_url=attachment_url
        )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/noticeboards/posts/<int:post_id>/view', methods=['POST'])
def api_record_post_view(post_id):
    """Record a view for a noticeboard post"""
    try:
        update_post_views(post_id)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/noticeboards/<int:noticeboard_id>/posts/<int:post_id>/pin', methods=['POST'])
def api_pin_post(noticeboard_id, post_id):
    """Pin a post to the top of the noticeboard"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    # Verify ownership
    noticeboard = get_noticeboard_details(noticeboard_id)
    if not noticeboard or noticeboard['owner_id'] != user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    try:
        result = pin_noticeboard_post(post_id, noticeboard_id)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/noticeboards/<int:noticeboard_id>/posts/<int:post_id>/unpin', methods=['POST'])
def api_unpin_post(noticeboard_id, post_id):
    """Unpin a post from the top of the noticeboard"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    # Verify ownership
    noticeboard = get_noticeboard_details(noticeboard_id)
    if not noticeboard or noticeboard['owner_id'] != user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    try:
        result = unpin_noticeboard_post(post_id, noticeboard_id)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/noticeboards/<int:noticeboard_id>/posts/<int:post_id>/delete', methods=['DELETE'])
def api_delete_post(noticeboard_id, post_id):
    """Delete a post from a noticeboard"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    # Verify ownership
    noticeboard = get_noticeboard_details(noticeboard_id)
    if not noticeboard or noticeboard['owner_id'] != user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    try:
        result = delete_noticeboard_post(post_id, noticeboard_id)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ========== NOTIFICATION API ENDPOINTS ==========

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Get user's notifications"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user_id = session['user_id']
    
    # Optional query parameters
    limit = request.args.get('limit', default=20, type=int)
    unread_only = request.args.get('unread_only', default=False, type=lambda x: x.lower() == 'true')
    
    # Validate limit
    if limit < 1 or limit > 100:
        limit = 20
    
    try:
        notifications = get_user_notifications(user_id, limit=limit, unread_only=unread_only)
        return jsonify({
            "success": True,
            "notifications": notifications,
            "count": len(notifications)
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/notifications/unread-count', methods=['GET'])
def get_unread_count():
    """Get count of unread notifications for current user"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user_id = session['user_id']
    
    try:
        count = get_unread_notification_count(user_id)
        return jsonify({
            "success": True,
            "unread_count": count
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """Mark a single notification as read"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        result = mark_notification_as_read(notification_id)
        if result:
            return jsonify({"success": True, "message": "Notification marked as read"}), 200
        else:
            return jsonify({"success": False, "message": "Failed to mark notification as read"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/notifications/read-all', methods=['POST'])
def mark_all_read():
    """Mark all notifications as read for current user"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user_id = session['user_id']
    
    try:
        result = mark_all_notifications_as_read(user_id)
        if result:
            return jsonify({"success": True, "message": "All notifications marked as read"}), 200
        else:
            return jsonify({"success": False, "message": "Failed to mark all notifications as read"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification_endpoint(notification_id):
    """Delete a notification"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        result = delete_notification(notification_id)
        if result:
            return jsonify({"success": True, "message": "Notification deleted"}), 200
        else:
            return jsonify({"success": False, "message": "Failed to delete notification"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
