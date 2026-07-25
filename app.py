from flask import Flask, render_template, redirect, session
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.student import student_bp

app = Flask(__name__)
app.secret_key = 'aiprobe-exam-system-secret-key-2026'

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(student_bp)


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/student/dashboard')
def student_dashboard():
    user = session.get('user')
    if not user or user.get('role') != 'student':
        return redirect('/login')
    return render_template('student/dashboard.html', user=user)


@app.route('/admin/dashboard')
def admin_dashboard():
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin/dashboard.html', user=user)


@app.route('/admin/exams')
def admin_exams():
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin/exams.html', user=user)

@app.route('/admin/questions')
def admin_questions():
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin/questions.html', user=user)

@app.route('/admin/users')
def admin_users():
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin/users.html', user=user)

@app.route('/admin/scores')
def admin_scores():
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin/scores.html', user=user)

@app.route('/admin/settings')
def admin_settings():
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin/settings.html', user=user)

@app.route('/student/exam')
def student_exam():
    user = session.get('user')
    if not user or user.get('role') != 'student':
        return redirect('/login')
    return render_template('student/exam.html', user=user)

@app.route('/student/practice')
def student_practice():
    user = session.get('user')
    if not user or user.get('role') != 'student':
        return redirect('/login')
    return render_template('student/practice.html', user=user)

@app.route('/student/records')
def student_records():
    user = session.get('user')
    if not user or user.get('role') != 'student':
        return redirect('/login')
    return render_template('student/records.html', user=user)

@app.route('/student/profile')
def student_profile():
    user = session.get('user')
    if not user or user.get('role') != 'student':
        return redirect('/login')
    return render_template('student/profile.html', user=user)

@app.route('/student/exam_paper')
def student_exam_paper():
    user = session.get('user')
    if not user or user.get('role') != 'student':
        return redirect('/login')
    return render_template('student/exam_paper.html', user=user)

@app.route('/student/result')
def student_result():
    user = session.get('user')
    if not user or user.get('role') != 'student':
        return redirect('/login')
    return render_template('student/result.html', user=user)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)