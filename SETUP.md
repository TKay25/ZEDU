# ZEDU Flask Setup - Quick Start Guide

## Step 1: Install Python Dependencies

Open PowerShell/Command Prompt in the ZEDU folder and run:

```bash
pip install -r requirements.txt
```

## Step 2: Run the Flask Application

```bash
python app.py
```

You should see output like:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

## Step 3: Open in Browser

Navigate to:
```
http://localhost:5000
```

## What You'll See

- **Landing Page** with modern dark theme
- **Sticky Navigation** with login buttons
- **Hero Section** with call-to-action
- **Features Section** with 4 key features
- **Courses Section** with 6 featured courses
- **User Types Section** for Students, Tutors, and Parents
- **Interactive Modals** for each login type
- **Professional Footer** with links and social icons

## File Structure

```
ZEDU/
├── app.py                    # Flask application
├── requirements.txt          # Python packages
├── README.md                 # Full documentation
├── SETUP.md                  # This file
└── templates/
    └── index.html           # Landing page
```

## Troubleshooting

**Port 5000 is already in use?**
```bash
python app.py --port 5001
```

**ModuleNotFoundError: No module named 'flask'?**
```bash
pip install Flask
```

**Template not loading?**
Make sure the `templates/` folder exists and contains `index.html`

## Next Steps

1. **Add Authentication**: Implement actual login functionality
2. **Connect Database**: Add SQLAlchemy for user management
3. **Add Pages**: Create student dashboard, tutor panel, parent portal
4. **Styling**: Customize colors and branding
5. **Deployment**: Deploy to Heroku, AWS, or other platforms

## Development Commands

```bash
# Run in debug mode (auto-reload)
python app.py

# Run with custom port
python app.py --port 5001

# Production-ready server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Enjoy building ZEDU! 🚀
