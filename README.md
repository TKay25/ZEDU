# ZEDU - Online Education Platform

A modern, responsive online education platform with user authentication, course management, and PostgreSQL database integration. Built with Flask, Bootstrap 5, and PostgreSQL.

## Features

- 🎓 **User Authentication**: Sign-up and login for Students, Tutors, and Parents
- 💾 **PostgreSQL Database**: Secure data storage with proper schema and indexes
- 🎨 **Modern Design**: Professional white background with deep blue and red accents
- 📱 **Fully Responsive**: Works perfectly on desktop, tablet, and mobile devices
- 🚀 **Flask Backend**: Python Flask for robust server-side functionality
- 📚 **6 Featured Courses**: Course showcase with pricing, ratings, and enrollment
- 👥 **Multi-tier Education Levels**: Primary School, High School, and University
- 🔐 **Secure Passwords**: SHA256 hashing for user passwords
- 📊 **Database Tables**: Users, Courses, Enrollments, Reviews

## Project Structure

```
ZEDU/
├── app.py                    # Flask application with auth endpoints
├── db_helper.py              # Database connection and helper functions
├── init_db.py                # Database initialization script
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── DATABASE_SETUP.md         # Detailed database documentation
├── templates/
│   └── index.html            # Landing page with sign-up/login modals
└── README.md                 # This file
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- pip (Python package manager)
- PostgreSQL database (provided)

### 2. Installation

**Clone or navigate to the project directory:**
```bash
cd ZEDU
```

**Create a virtual environment (optional but recommended):**
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

### 3. Initialize Database

**Run the database initialization script:**
```bash
python init_db.py
```

This will:
- Test the database connection
- Create all necessary tables (users, courses, enrollments, reviews)
- Create performance indexes

### 4. Running the Application

**Start the Flask development server:**
```bash
python app.py
```

**Open your browser and navigate to:**
```
http://localhost:5000
```

You should see the ZEDU landing page with sign-up and login modals!

## Database

### Overview
ZEDU uses PostgreSQL for persistent data storage. The database includes:

- **users** table: Stores user accounts (students, tutors, parents)
- **courses** table: Stores course information created by tutors
- **enrollments** table: Tracks student enrollment in courses
- **reviews** table: Stores course reviews and ratings

### Connection String
```
postgresql://zeduweb_user:qdEe6bfJmlIHAknO2TVbum3SSm2kFvFV@dpg-d7cklfa8qa3s73e9podg-a.oregon-postgres.render.com/zeduweb
```

For detailed database documentation, see [DATABASE_SETUP.md](DATABASE_SETUP.md)

## Authentication System

### Sign Up
1. Click the "Sign Up" link on the landing page
2. Fill in: Full Name, Email, Role (Student/Tutor/Parent), Password
3. If Student, select Education Level
4. Click "Create Account"
5. Success! You can now log in

### Login
1. Click the appropriate login button (Student/Tutor/Parent)
2. Enter email and password
3. Click "Sign In"
4. Session is created and you're authenticated

### API Endpoints
- `POST /api/signup` - Create new user account
- `POST /api/login` - Authenticate user
- `POST /api/logout` - Log out user
- `GET /api/profile` - Get current user profile
- `GET /api/tutors` - Get list of tutors

See [DATABASE_SETUP.md](DATABASE_SETUP.md) for detailed API documentation

## Files Overview

### app.py
Flask application with the following endpoints:
- `/` - Landing page
- `/api/signup` - User registration
- `/api/login` - User authentication
- `/api/logout` - Logout user
- `/api/profile` - Get user profile
- `/api/tutors` - Get tutors list

### db_helper.py
Database helper functions including:
- `get_db_connection()` - Establish database connection
- `create_tables()` - Initialize database schema
- `create_user()` - Create new user account
- `authenticate_user()` - Verify user credentials
- `hash_password()` - Hash passwords securely
- `verify_password()` - Verify password against hash
- `get_tutors()` - Retrieve tutors list
- And more...

### init_db.py
One-time database initialization script. Run this once after installation to create all tables and indexes.

### templates/index.html
Single-page landing template including:
- Responsive navigation with dropdown menus
- Sign-up modal with form validation
- Student, Tutor, and Parent login modals
- Course showcase
- Instructor profiles
- FAQ section
- Newsletter subscription
- Smooth animations and transitions

## Features Explained

### Login Modals
- **Student Login**: For learners to access courses
- **Tutor Login**: For instructors to manage courses
- **Parent Login**: For parents to monitor student progress

### Sections

1. **Navigation Bar**: Sticky header with quick links and login buttons
2. **Hero Section**: Eye-catching headline with CTA buttons
3. **Features Section**: Highlights of the platform (4 features)
4. **Courses Section**: 6 featured courses with pricing
5. **User Types Section**: Detailed information for each user type
6. **CTA Section**: Final call-to-action
7. **Footer**: Links, social media, and company info

## Customization

### Colors
Edit the CSS variables in `templates/index.html`:
```css
--primary-blue: #0a1e3d;      /* Deep dark blue */
--secondary-red: #8b1a1a;     /* Deep dark red */
--accent-blue: #1e3a8a;
--light-bg: #ffffff;
--light-bg-alt: #f8f9fa;
--text-dark: #1a1a1a;
--text-gray: #666666;
--border-light: #e0e0e0;
```

### Content
Edit course information, instructor profiles, and testimonials in `templates/index.html`

### Database
To add new tables or fields:
1. Update the schema in `db_helper.py` (create_tables function)
2. Re-run `python init_db.py`
3. Or manually add columns/tables using PostgreSQL client

### API Routes
Add new endpoints in `app.py`:
```python
@app.route('/api/my-endpoint', methods=['POST'])
def my_endpoint():
    # Your code here
    return jsonify({"success": True}), 200
```

## Future Features

- ✅ User Authentication (Implemented)
- ✅ Database Integration (Implemented)
- 🔄 Email Verification
- 🔄 Course Creation Dashboard for Tutors
- 🔄 Student Course Progress Tracking
- 🔄 Parent Monitoring Dashboard
- 🔄 Payment Integration
- 🔄 Real-time Notifications
- 🔄 Video Streaming Support
- 🔄 Certificate Generation

## Deployment

### Using Gunicorn (Recommended for Production)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Render
1. Push code to GitHub
2. Create new Web Service on Render.com
3. Connect GitHub repository
4. Set environment variables in Render dashboard
5. Deploy!

### Security Checklist for Production
- [ ] Change `SECRET_KEY` in `app.py`
- [ ] Set `FLASK_ENV=production`
- [ ] Use environment variables for sensitive data
- [ ] Enable HTTPS
- [ ] Set secure session cookies
- [ ] Add CSRF protection
- [ ] Use strong database passwords
- [ ] Enable rate limiting

## Troubleshooting

### Database Connection Error
**Error**: "could not connect to server"
- Verify the database connection string in `db_helper.py`
- Ensure your internet connection is working
- Check that PostgreSQL server is accessible

### Tables Don't Exist
**Error**: "relation 'users' does not exist"
- Run `python init_db.py` to initialize the database
- Verify the script output shows successful table creation

### Email Already Registered
**Error**: "Email already registered"
- Use a different email address for sign-up
- Or log in with your existing account

### Port Already in Use
**Error**: "Address already in use"
```bash
# Run on a different port
python app.py
# Then modify app.run(port=5001)
```

### Sign-up Form Not Submitting
- Check browser console for JavaScript errors (F12 → Console)
- Verify database is initialized with `python init_db.py`
- Ensure all required fields are filled in

### Password Hash Not Matching
- Passwords are hashed using SHA256
- Ensure no whitespace is being added to passwords
- Clear browser cache and try again

## Technologies Used

- **Frontend**: HTML5, CSS3, Bootstrap 5, Font Awesome Icons
- **Backend**: Python Flask
- **Design**: Modern gradient-based UI with smooth animations

## Future Enhancements

- [ ] User authentication system
- [ ] Database integration (PostgreSQL/MySQL)
- [ ] Course enrollment functionality
- [ ] Payment gateway integration
- [ ] Student dashboard
- [ ] Tutor course creation panel
- [ ] Parent monitoring dashboard
- [ ] Video course hosting
- [ ] Interactive quizzes
- [ ] Certificate generation

## License

This project is open source and available under the MIT License.

## Support

For support, please create an issue in the GitHub repository.

---

**Made with ❤️ for the future of education**
