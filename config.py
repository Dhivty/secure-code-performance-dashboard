# In config.py
import os
DB_PATH = os.getenv('DB_PATH', os.path.join('db', 'user_db.db'))
DB_DIR = 'db'
USER_LOG_EXCEL = 'user_signups.xlsx'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'py', 'sql'}
REPORTS_DIR = 'reports'