import sqlite3
import logging
import base64
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('issues.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Create issues table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS issues (
        id TEXT PRIMARY KEY,
        label TEXT,
        type TEXT,
        description TEXT,
        severity TEXT,
        status TEXT,
        timeframe TEXT,
        action_taken TEXT,
        costusd TEXT,
        savedusd TEXT,
        recommended_contact TEXT,
        updated_at TEXT,
        version TEXT,
        latitude REAL,
        longitude REAL,
        created_at TEXT,
        creator_id TEXT,
        creator_name TEXT
    )
    ''')

    # Create images table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS images (
        submission_id TEXT PRIMARY KEY,
        title TEXT,
        label TEXT,
        image BLOB
    )
    ''')

    # Create responses table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS responses (
        SubmissionDate TEXT,
        entity_problem TEXT,
        action_role TEXT,
        action_status TEXT,
        action_action_taken TEXT,
        action_image BLOB,
        action_resolution_costusd TEXT,
        action_resolution_timeframe TEXT,
        action_recommended_contact TEXT,
        "KEY" TEXT PRIMARY KEY,
        SubmitterName TEXT
    )
    ''')

    conn.commit()
    conn.close()

def insert_or_update_issue(issue_data):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
        INSERT OR REPLACE INTO issues (
            id, label, type, description, severity, status, timeframe, action_taken,
            costusd, savedusd, recommended_contact, updated_at, version, latitude, longitude,
            created_at, creator_id, creator_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            issue_data['id'], issue_data['label'], issue_data['type'], issue_data['description'],
            issue_data['severity'], issue_data['status'], issue_data['timeframe'], issue_data['action_taken'],
            issue_data['costusd'], issue_data['savedusd'], issue_data['recommended_contact'],
            issue_data['updated_at'], issue_data['version'], issue_data['latitude'], issue_data['longitude'],
            issue_data['created_at'], issue_data['creator_id'], issue_data['creator_name']
        ))
        conn.commit()
        logging.info(f"Issue {issue_data['id']} inserted/updated successfully.")
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
    finally:
        conn.close()

def insert_image(submission_id, title, label, image_data):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''
            INSERT OR IGNORE INTO images (submission_id, title, label, image) VALUES (?, ?, ?, ?)
            ''', (submission_id, title, label, image_data))
        conn.commit()
        logging.info(f"Image '{title}' inserted successfully for submission ID {submission_id}.")
    except sqlite3.Error as e:
        logging.error(f"Database error during insert_image: {e}")
    finally:
        conn.close()

def insert_response(response):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''
            INSERT OR REPLACE INTO responses (
                SubmissionDate,
                entity_problem,
                action_role,
                action_status,
                action_action_taken,
                action_image,
                action_resolution_costusd,
                action_resolution_timeframe,
                action_recommended_contact,
                "KEY",
                SubmitterName
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                response.get('SubmissionDate'),
                response.get('entity_problem'),
                response.get('action_role'),
                response.get('action_status'),
                response.get('action_action_taken'),
                response.get('action_image'),
                response.get('action_resolution_costusd'),
                response.get('action_resolution_timeframe'),
                response.get('action_recommended_contact'),
                response.get('KEY'),
                response.get('SubmitterName')
            )
        )
        conn.commit()
        logging.info(f"Response with KEY {response.get('KEY')} inserted/updated successfully.")
    except sqlite3.Error as e:
        logging.error(f"Database error during insert_response: {e}")
    finally:
        conn.close()

def get_issues_with_images(search_query='', state_filter='', severity_filter='', timeframe_filter='', start_date='', end_date=''):
    conn = get_db_connection()
    cur = conn.cursor()

    query = '''
        SELECT issues.*, images.image
        FROM issues
        LEFT JOIN images ON issues.label = images.title
        WHERE 1=1
    '''
    params = []

    # Existing filters
    if search_query:
        query += ' AND (LOWER(issues.label) LIKE ? OR LOWER(issues.description) LIKE ? OR LOWER(issues.type) LIKE ?)'
        params.extend(['%' + search_query.lower() + '%'] * 3)

    if state_filter:
        query += ' AND LOWER(issues.status) = ?'
        params.append(state_filter.lower())

    if severity_filter:
        query += ' AND LOWER(issues.severity) = ?'
        params.append(severity_filter.lower())

    if timeframe_filter:
        query += ' AND LOWER(issues.timeframe) = ?'
        params.append(timeframe_filter.lower())

    # Apply date filters on created_at
    if start_date:
        query += ' AND DATE(issues.created_at) >= DATE(?)'
        params.append(start_date)

    if end_date:
        query += ' AND DATE(issues.created_at) <= DATE(?)'
        params.append(end_date)

    logging.info(f"Executing query: {query} with params: {params}")

    cur.execute(query, params)
    # ... rest of the code ...


    cur.execute(query, params)
    rows = cur.fetchall()

    issues = []
    for row in rows:
        issue = dict(row)
        if issue['image']:
            issue['image'] = base64.b64encode(issue['image']).decode('utf-8')  # Convert image to base64
        else:
            issue['image'] = None
        issues.append(issue)

    conn.close()
    return issues

def get_responses_for_issue(issue_id):
    conn = get_db_connection()
    cur = conn.cursor()

    query = '''
        SELECT *
        FROM responses
        WHERE entity_problem = ?
        ORDER BY SubmissionDate DESC
    '''

    cur.execute(query, (issue_id,))
    rows = cur.fetchall()

    responses = []
    for row in rows:
        response = dict(row)
        if response['action_image']:
            response['action_image'] = base64.b64encode(response['action_image']).decode('utf-8')
        else:
            response['action_image'] = None
        responses.append(response)

    conn.close()
    return responses

def get_latest_update_time():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT MAX(updated_at) as latest_update FROM issues')
    result = cur.fetchone()
    conn.close()
    if result and result['latest_update']:
        return datetime.fromisoformat(result['latest_update'])
    return None

if __name__ == "__main__":
    # Initialize the database and ensure tables exist
    init_db()
    logging.info("Database setup complete.")
