**Performance Dashboard Application**

**Overview**

This is a web-based application designed to track the performance and security of Python and SQL scripts. It allows users to upload files, analyze their execution metrics, and generate security reports.

**Features**

User authentication (login/signup/logout)
File upload for Python (.py) and SQL (.sql) scripts
Performance tracking (execution time, peak memory, response time, throughput)
Security analysis with risk assessment
Historical performance and security data visualization
Admin functionality to view all users

**Prerequisites**
Python 3.x
Required Python packages (listed in requirements.txt)

**Installation**

1.Clone the repository:
git clone https://github.com/yourusername/performance-dashboard.git
cd performance-dashboard


2.Install dependencies:
pip install -r requirements.txt


3.Set up the database and directories:

Ensure the db and static/uploads directories exist or are created automatically on first run.
The application will initialize the SQLite database on startup.


4.Run the application:
python app.py


5.Access the application at http://localhost:5000.


**Configuration**

Edit config.py to adjust database path (DB_PATH), upload folder (UPLOAD_FOLDER), and allowed file extensions (ALLOWED_EXTENSIONS).

**Usage**

Sign up or log in to access the dashboard.
Upload Python or SQL files to analyze their performance and security.
View historical data and detailed reports on the dashboard.

