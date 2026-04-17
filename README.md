# ZEDU - Online Education Platform

A modern, responsive landing page for an online education platform built with Flask and Bootstrap 5.

## Features

- 🎓 **Multiple User Types**: Student, Tutor, and Parent login portals
- 🎨 **Modern Design**: Deep dark blue and deep dark red theme with smooth animations
- 📱 **Fully Responsive**: Works perfectly on desktop, tablet, and mobile devices
- 🚀 **Flask Backend**: Python Flask for server-side rendering
- 📚 **6 Featured Courses**: Course showcase with pricing and enrollment
- 👥 **User-Type Cards**: Dedicated sections for each user type

## Project Structure

```
ZEDU/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Landing page template
├── static/
│   ├── css/              # Custom CSS (if needed)
│   └── js/               # Custom JavaScript (if needed)
└── README.md             # This file
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- pip (Python package manager)

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

### 3. Running the Application

**Start the Flask development server:**
```bash
python app.py
```

**Open your browser and navigate to:**
```
http://localhost:5000
```

You should see the ZEDU landing page!

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
--primary-dark: #0a1e3d;      /* Deep dark blue */
--secondary-dark: #8b1a1a;    /* Deep dark red */
--accent-light: #1e3a8a;
--text-light: #e0e7ff;
```

### Content
Edit course information, features, and user descriptions in the HTML template.

### Routes
Add new routes in `app.py` for additional functionality (authentication, enrollment, etc.)

## Adding Authentication

To add actual login functionality:

1. Install additional packages:
```bash
pip install Flask-Login Flask-SQLAlchemy
```

2. Create a database models file
3. Update the login forms to POST to proper endpoints
4. Implement session management

## Deployment

### Using Gunicorn (Recommended for Production)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Heroku
1. Create `Procfile`:
```
web: gunicorn app:app
```

2. Deploy:
```bash
heroku create
git push heroku main
```

## Troubleshooting

**Port already in use:**
```bash
python app.py --port 5001
```

**Template not found:**
Ensure the `templates/` folder exists and contains `index.html`

**Static files not loading:**
Make sure to create a `static/` folder if using custom CSS/JS

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
