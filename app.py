from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import os
from werkzeug.utils import secure_filename
from datetime import timedelta
from auth import login_user, signup_user, get_user_id, init_user_db, log_file_upload
import sqlite3
from flask import current_app
from config import DB_PATH, UPLOAD_FOLDER, ALLOWED_EXTENSIONS

from report import (
    run_python, 
    run_sql, 
    save_performance_report, 
    get_user_history,
    generate_security_report,
    save_combined_report,
    log_execution
)
# Configuration


app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure random key
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_COOKIE_SECURE'] = False  # True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def check_login():
    allowed_routes = ['login', 'signup', 'static', 'home']
    if request.endpoint in allowed_routes:
        return
    if 'username' not in session:
        return redirect(url_for('login'))

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'username' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        success, message = signup_user(username, password)
        if success:
            flash(message, "success")
            return redirect(url_for('login'))
        else:
            flash(message, "error")
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if login_user(username, password):
            session['username'] = username
            session.permanent = True
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for('dashboard'))
        flash("Invalid credentials. Please try again.", "error")
    return render_template('login.html')
@app.route('/dashboard')
def dashboard():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    
    try:
        history = get_user_history(username)
        print(f"History for {username}:", history)  # Debug print
        return render_template('dashboard.html', username=username, history=history)
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {str(e)}")
        flash("Error loading history", "error")
        return render_template('dashboard.html', username=username, history=None)
@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    username = session['username']
    user_id = get_user_id(username)
    
    # Create user-specific upload directory
    user_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], username)
    os.makedirs(user_upload_dir, exist_ok=True)
    
    if 'file' not in request.files:
        flash("No file selected", "error")
        return redirect(url_for('dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(url_for('dashboard'))
    
    if not allowed_file(file.filename):
        flash("Only .py or .sql files allowed", "error")
        return redirect(url_for('dashboard'))
    
    try:
        filename = secure_filename(file.filename)
        save_path = os.path.join(user_upload_dir, filename)
        file.save(save_path)
        
        filetype = filename.rsplit('.', 1)[1].lower()
        
        # Log the file upload in database - FIXED LINE BELOW
        if not log_file_upload(username, filename, save_path, filetype):  # Now passing all 4 arguments
            flash("Error logging file upload", "error")
            return redirect(url_for('dashboard'))
        
        # Rest of your upload processing...
        
        # Run the file and get performance metrics
        report = run_python(save_path, username) if filetype == 'py' else run_sql(save_path, username)
        
        if not report:
            flash("Error executing file", "error")
            return redirect(url_for('dashboard'))
            
        # Generate security report
        security_report = generate_security_report(save_path, filetype)
        
        # Save combined report
        save_combined_report(report, security_report, username)
        
        # Save performance data separately (for history)
        save_performance_report(report, username)
        
        # Log execution with security metrics
        user_id = get_user_id(username)
        if user_id:
            log_execution(
                user_id, 
                filename, 
                report.get('exec_time'), 
                report.get('peak_memory'),
                security_report.get('security_score'),
                security_report.get('risk_level'),
                security_report.get('security_issues')
            )
        
        # Render report with both performance and security data
        return render_template('security_report.html', 
                            report=report,
                            security=security_report)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        current_app.logger.error(f"Upload error: {str(e)}")
    return redirect(url_for('dashboard'))
@app.route('/rerun/<filename>')
def rerun(filename):
    username = session['username']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], username, filename)  # Include username in path
    if not os.path.exists(filepath):
        flash("File not found", "error")
        return redirect(url_for('dashboard'))
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    try:
        # Run the file and get performance metrics
        report = run_python(filepath, username) if ext == 'py' else run_sql(filepath, username)
        
        if report:
            # Generate security report
            security_report = generate_security_report(filepath, ext)
            
            # Save combined report
            save_combined_report(report, security_report, username)
            
            # Save performance data
            save_performance_report(report, username)
            
            # Log execution with security metrics
            user_id = get_user_id(username)
            if user_id:
                log_execution(
                    user_id, 
                    filename, 
                    report['exec_time'], 
                    report['peak_memory'],
                    security_report['security_score'],
                    security_report['risk_level'],
                    security_report['security_issues']
                )
            
            return render_template('security_report.html', 
                                report=report,
                                security=security_report)
    except Exception as e:
        current_app.logger.error(f"Rerun error: {str(e)}")
    
    flash("Error rerunning file", "error")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    username = session.get('username', 'User')
    session.clear()
    response = make_response(render_template('logout.html', username=username))
    response.set_cookie('session', '', expires=0)
    return response
@app.route('/report/<filename>')
def report_details(filename):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    
    try:
        # Get the latest execution of this file by the user
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.execution_time, r.memory_usage, r.security_score, r.risk_level, r.security_issues
                FROM run_logs r
                JOIN files f ON r.file_id = f.file_id
                JOIN users u ON r.user_id = u.id
                WHERE u.username = ? AND f.filename = ?
                ORDER BY r.timestamp DESC
                LIMIT 1
            ''', (username, filename))
            
            result = cursor.fetchone()
            if result:
                report = {
                    'filename': filename,
                    'exec_time': result[0],
                    'peak_memory': result[1],
                    'response_time': round(result[0] * 1000, 2),
                    'throughput': round(1 / result[0], 2) if result[0] else 'N/A'
                }
                security_report = {
                    'security_score': result[2],
                    'risk_level': result[3],
                    'security_issues': eval(result[4]) if result[4] else [],
                    'vulnerability_count': len(eval(result[4])) if result[4] else 0
                }
                return render_template('security_report.html', 
                                    report=report,
                                    security=security_report)
    
    except Exception as e:
        flash(f"Error retrieving report: {str(e)}", "error")
    
    return redirect(url_for('dashboard'))
def check_db_tables():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Existing tables:", tables)

if __name__ == "__main__":
    os.makedirs('db', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    init_user_db()
    app.run(debug=True, port=5000)