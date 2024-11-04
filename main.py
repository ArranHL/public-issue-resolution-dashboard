from flask import Flask, render_template, jsonify, request
from database import get_issues_with_images, get_responses_for_issue, init_db
import logging
import traceback
from utils.odk_api import ODKAPI
from flask_socketio import SocketIO
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
socketio = SocketIO(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_data():
    try:
        init_db()
        api = ODKAPI()
        api.update_existing_issues_and_responses()
        app.logger.info("Initial data loaded successfully")
        socketio.emit('data_updated', {'message': 'Data has been updated'})
    except Exception as e:
        app.logger.error(f"Error during initialization: {str(e)}")
        app.logger.error(traceback.format_exc())

def scheduled_data_refresh():
    try:
        logging.info("Starting scheduled data refresh")
        api = ODKAPI()
        api.update_existing_issues_and_responses()
        logging.info("Scheduled data refresh completed successfully")
        socketio.emit('data_updated', {'message': 'Data has been updated'})
    except Exception as e:
        logging.error(f"Error during scheduled data refresh: {str(e)}")
        logging.error(traceback.format_exc())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/kanban')
def kanban():
    return render_template('kanban.html')

@app.route('/theory_of_change')
def theory_of_change():
    return render_template('theory_of_change.html')

@app.route('/project_data')
def project_data():
    return render_template('project_data.html')

@app.route('/api/issues', methods=['GET'])
def get_issues():
    try:
        # Retrieve filters from query parameters and normalize them
        search_query = request.args.get('search', '').strip().lower()
        state_filter = request.args.get('state', '').strip().lower()
        severity_filter = request.args.get('severity', '').strip().lower()
        timeframe_filter = request.args.get('timeframe', '').strip().lower()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        logging.info(f"Received filters: search='{search_query}', state='{state_filter}', severity='{severity_filter}', timeframe='{timeframe_filter}', start_date='{start_date}', end_date='{end_date}'")

        # Pass all relevant filters to the function
        issues_with_images = get_issues_with_images(
            search_query=search_query,
            state_filter=state_filter,
            severity_filter=severity_filter,
            timeframe_filter=timeframe_filter,
            start_date=start_date,
            end_date=end_date
        )

        for issue in issues_with_images:
            # Check if the issue has any responses
            responses = get_responses_for_issue(issue['id'])
            if not responses:
                issue['status'] = 'new'
            status_mapping = {
                'new': 'new',
                'open': 'open',
                'waiting': 'waiting',
                'fixed': 'fixed',
            }
            issue['status'] = status_mapping.get(issue['status'].lower(), 'new')
            # Ensure created_at is included in the response
            if 'created_at' not in issue:
                issue['created_at'] = issue.get('updated_at', 'Unknown')

        logging.info(f"Returning {len(issues_with_images)} issues")
        return jsonify(issues_with_images)
    except Exception as e:
        logging.error(f"Error fetching issues: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An error occurred while fetching issues"}), 500

@app.route('/api/responses/<issue_id>', methods=['GET'])
def get_responses(issue_id):
    try:
        responses = get_responses_for_issue(issue_id)
        return jsonify(responses)
    except Exception as e:
        logging.error(f"Error fetching responses for issue {issue_id}: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An error occurred while fetching responses"}), 500

@app.route('/update_odk', methods=['GET'])
def update_odk():
    try:
        logging.info("Starting ODK data update process")
        api = ODKAPI()
        result = api.update_existing_issues_and_responses()
        logging.info(f"ODK update completed. Updated issues: {len(result.get('issues', []))}, Updated images: {len(result.get('images', []))}")
        return jsonify({
            "message": "ODK update completed successfully",
            "updated_issues": len(result.get('issues', [])),
            "updated_images": len(result.get('images', []))
        })
    except Exception as e:
        logging.error(f"Error in update_odk route: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An error occurred while updating ODK data"}), 500

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    jobs = scheduler.get_jobs()
    job_details = []
    for job in jobs:
        job_details.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })
    return jsonify(job_details)

if __name__ == '__main__':
    initialize_data()
    
    # Set up the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_data_refresh, 'interval', hours=1)  # Adjust the interval as needed
    scheduler.start()
    
    socketio.run(app)
