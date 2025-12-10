# logs file generator usage
python audit_generator.py

# Prepopulate 3 days of logs (50 entries each), then run live with daily rotation
python audit_generator.py --file ue_audit.log --rotation day --prepopulate 3 --entries 50

# Prepopulate 2 days of logs, then run live with size-based rotation (100 KB per file)
python audit_generator.py --file ue_audit.log --rotation size --maxsize 100000 --prepopulate 2

python audit_generator.py --file ue_audit.log --rotation size --maxsize 100000 --prepopulate 2 --entries 100000

# start simple python http server
Under the log directory
python3 -m http.server 8000

# How to Run with PostgreSQL
#     Install PostgreSQL (Ubuntu example):

sudo apt update

sudo apt install postgresql postgresql-contrib -y

# Create database and user
sudo -u postgres psql

CREATE DATABASE logsdb;

CREATE USER postgres WITH PASSWORD 'postgres';

GRANT ALL PRIVILEGES ON DATABASE logsdb TO postgres;

\q

# Set environment variable:

export SQLALCHEMY_DATABASE_URI="postgresql://postgres:postgres@localhost:5432/logsdb"
export REMOTE_LOG_URL="https://localhost:8000/ue_audit_1.log"

# How to Use the REST API
- Get all logs
   GET http://localhost:5000/api/logs

- Filter by user
  GET http://localhost:5000/api/logs?user=Alice

- Filter by date
  GET http://localhost:5000/api/logs?date=2025-12-01

- Filter by both
  GET http://localhost:5000/api/logs?user=John&date=2025-12-05
  
- Response example:
  
  [
    {
      "timestamp": "2025-12-01T13:02:33",
      "level": "INFO",
      "user": "Alice",
      "message": "Login successful",
      "role": "Manager"
  }
]



