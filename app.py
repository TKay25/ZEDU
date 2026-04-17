from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def landing():
    """Render the landing page"""
    return render_template('index.html')

@app.route('/student-login')
def student_login():
    """Student login endpoint"""
    return {'status': 'Student login page'}

@app.route('/tutor-login')
def tutor_login():
    """Tutor login endpoint"""
    return {'status': 'Tutor login page'}

@app.route('/parent-login')
def parent_login():
    """Parent login endpoint"""
    return {'status': 'Parent login page'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
