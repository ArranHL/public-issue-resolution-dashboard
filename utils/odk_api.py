from dotenv import load_dotenv
import os
import json
import requests
import traceback
import logging
from datetime import datetime
from flask import Flask
from flask_socketio import SocketIO
from urllib.parse import urljoin
from database import (
    insert_or_update_issue,
    insert_image,
    insert_response,
    init_db
)

# Load environment variables from .env file
# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)



# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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

class ODKAPI:
    def __init__(self):
        self.base_url = "https://integrityaction.net"
        self.session_token = None
        self.login()

    def login(self):
        login_url = urljoin(self.base_url, 'v1/sessions')
        credentials = {
            "email": os.getenv('API_EMAIL'),
            "password": os.getenv('API_PASSWORD')
        }
        try:
            logging.info("Attempting to log in to ODK API.")
            response = requests.post(login_url, json=credentials)
            logging.debug(f"Login response: {response.status_code} - {response.text}")
            response.raise_for_status()
            self.session_token = response.json().get('token')
            if not self.session_token:
                logging.error("No token found in login response.")
                raise ValueError("Authentication failed: No token provided.")
            logging.info("Login successful.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Login failed: {str(e)}")
            logging.error(traceback.format_exc())
            raise

    def _make_request(self, endpoint, method="GET", params=None, is_binary=False):
        headers = {
            "Authorization": f"Bearer {self.session_token}",
        }
        if not is_binary:
            headers["Content-Type"] = "application/json"

        if endpoint.startswith('http://') or endpoint.startswith('https://'):
            url = endpoint
        else:
            url = urljoin(self.base_url + '/', endpoint.lstrip('/'))

        try:
            logging.debug(f"Making API request: {method} {url}")
            if params:
                logging.debug(f"Request parameters: {json.dumps(params)}")

            response = requests.request(method, url, headers=headers, params=params)
            logging.debug(f"API response status code: {response.status_code}")
            logging.debug(f"API response content: {response.text}")

            response.raise_for_status()
            if is_binary:
                logging.debug("Received binary data.")
                return response.content
            else:
                response_json = response.json()
                logging.debug(f"Received JSON response: {json.dumps(response_json, indent=2)}")
                return response_json
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {str(e)}")
            logging.error(traceback.format_exc())
            if 'response' in locals() and response is not None:
                try:
                    logging.error(f"Response content: {response.content.decode()}")
                except:
                    logging.error("Failed to decode response content.")
            raise

    def get_new_issues(self):
        logging.info("Fetching new issues from ODK API.")
        try:
            entities = self.fetch_entities()
            processed_entities = self.process_entities(entities)
            new_or_updated_issues = self.update_issues(processed_entities)
            return new_or_updated_issues
        except Exception as e:
            logging.error(f"Failed to fetch new issues: {str(e)}")
            logging.error(traceback.format_exc())
            return []

    def fetch_entities(self):
        endpoint = 'v1/projects/2/datasets/problems.svc/Entities'
        return self._make_request(endpoint)

    def process_entities(self, entities):
        logging.info("Processing entities.")
        processed_entities = {}
        for entity in entities.get('value', []):
            issue_id = entity.get('__id')
            if not issue_id:
                logging.warning("Entity without __id encountered.")
                continue

            # Log raw entity data for debugging
            logging.debug(f"Raw entity data: {json.dumps(entity, indent=2)}")

            processed_entities[issue_id] = {
                'id': issue_id,
                'label': entity.get('label', 'Untitled Issue'),
                'type': entity.get('type', 'Unknown'),
                'description': entity.get('description', 'No Description'),
                'severity': entity.get('severity', 'Not Specified'),
                'status': entity.get('status', 'new'),  # Set default status to 'new'
                'timeframe': entity.get('timeframe', 'No Timeframe'),
                'action_taken': entity.get('action_taken', 'No Action Taken'),
                'costusd': entity.get('costusd', '0'),
                'savedusd': entity.get('savedusd', 'N/A'),
                'recommended_contact': entity.get('recommended_contact', 'No Contact'),
                'created_at': self._format_date(entity.get('__system', {}).get('createdAt')),
                'updated_at': self._format_date(entity.get('__system', {}).get('updatedAt')),
                'creator_id': entity.get('__system', {}).get('creatorId', 'Unknown'),
                'creator_name': entity.get('__system', {}).get('creatorName', 'Unknown'),
                'version': str(entity.get('__system', {}).get('version', 'No Version')),
                'latitude': None,
                'longitude': None
            }
            geometry = entity.get('geometry', '').split()
            if geometry and len(geometry) >= 2:
                try:
                    processed_entities[issue_id]['latitude'], processed_entities[issue_id]['longitude'] = map(float, geometry[:2])
                except ValueError:
                    processed_entities[issue_id]['latitude'] = None
                    processed_entities[issue_id]['longitude'] = None
                    logging.warning(f"Invalid geometry data in entity for issue {issue_id}: {geometry}")
            else:
                logging.warning(f"No geometry data found in entity for issue {issue_id}.")
        return processed_entities

    def update_issues(self, processed_entities):
        logging.info("Updating issues in the database.")
        new_or_updated_issues = []
        for issue_id, issue_data in processed_entities.items():
            logging.debug(f"Processing issue ID: {issue_id}")
            # Log the issue data before insertion
            logging.debug(f"Issue data to insert/update: {json.dumps(issue_data, indent=2)}")
            try:
                insert_or_update_issue(issue_data)
                new_or_updated_issues.append(issue_data)
            except Exception as e:
                logging.error(f"Error inserting/updating issue {issue_id}: {str(e)}")
                logging.error(traceback.format_exc())
        logging.info(f"Number of new or updated issues: {len(new_or_updated_issues)}")
        return new_or_updated_issues

    def fetch_responses(self):
        logging.info("Fetching responses from ODK API.")
        try:
            submissions = self.fetch_response_submissions()
            processed_responses = self.process_responses(submissions)
            self.save_responses(processed_responses)
            logging.info(f"Fetched and stored {len(processed_responses)} new responses from ODK API.")
        except Exception as e:
            logging.error(f"Failed to fetch responses: {str(e)}")
            logging.error(traceback.format_exc())

    def fetch_response_submissions(self):
        endpoint = 'v1/projects/2/forms/address_problem.svc/Submissions'
        return self._make_request(endpoint)

    def process_responses(self, submissions):
        logging.info("Processing responses from submissions.")
        processed_responses = []

        for submission in submissions.get('value', []):
            logging.debug(f"Processing submission: {json.dumps(submission, indent=2)}")

            response_data = {}
            response_data['SubmissionDate'] = self._format_date(submission.get('__system', {}).get('submissionDate'))
            response_data['KEY'] = submission.get('__id')
            response_data['SubmitterName'] = submission.get('__system', {}).get('submitterName')

            response_data['entity_problem'] = submission.get('entity', {}).get('problem')
            logging.debug(f"Extracted entity_problem: {response_data['entity_problem']} for submission: {response_data['KEY']}")

            action = submission.get('action', {})
            logging.debug(f"Action group for submission {response_data['KEY']}: {json.dumps(action, indent=2)}")

            response_data['action_role'] = action.get('role')
            response_data['action_status'] = action.get('status')
            response_data['action_action_taken'] = action.get('action_taken')
            response_data['action_resolution_costusd'] = action.get('resolution_costusd')
            response_data['action_resolution_timeframe'] = action.get('resolution_timeframe')
            response_data['action_recommended_contact'] = action.get('recommended_contact')

            action_image_filename = action.get('image')
            if action_image_filename:
                submission_id = submission.get('__id')
                image_endpoint = f'v1/projects/2/forms/address_problem/submissions/{submission_id}/attachments/{action_image_filename}'
                logging.debug(f"Constructed image endpoint: {image_endpoint} for submission {submission_id}")
                try:
                    action_image_data = self.download_image(image_endpoint)
                    response_data['action_image'] = action_image_data
                    logging.debug(f"Image downloaded successfully for submission {submission_id}.")
                except Exception as e:
                    logging.error(f"Failed to download action image for submission {submission_id}: {str(e)}")
                    logging.error(traceback.format_exc())
                    response_data['action_image'] = None
            else:
                logging.info(f"No action image found for submission {submission.get('__id')}.")
                response_data['action_image'] = None

            response_data_for_logging = {k: v for k, v in response_data.items() if k != 'action_image'}
            logging.debug(f"Processed response data: {json.dumps(response_data_for_logging, indent=2)}")

            processed_responses.append(response_data)
        return processed_responses

    def save_responses(self, processed_responses):
        logging.info("Saving responses to the database.")
        for response in processed_responses:
            try:
                insert_response(response)
                logging.info(f"Response with KEY {response.get('KEY')} saved successfully.")
            except Exception as e:
                logging.error(f"Failed to save response with KEY {response.get('KEY')}: {str(e)}")
                logging.error(traceback.format_exc())
                continue

    def get_images(self):
        logging.info("Fetching images from submissions.")
        try:
            submissions = self.fetch_image_submissions()
            processed_images = self.process_images(submissions)
            self.save_images(processed_images)
            logging.info(f"Fetched and stored {len(processed_images)} new images from ODK API.")
            return processed_images
        except Exception as e:
            logging.error(f"Failed to fetch images: {str(e)}")
            logging.error(traceback.format_exc())
            return []

    def fetch_image_submissions(self):
        endpoint = 'v1/projects/2/forms/report_problem.svc/Submissions'
        return self._make_request(endpoint)

    def process_images(self, submissions):
        logging.info("Processing images from submissions.")
        processed_images = {}
        for submission in submissions.get('value', []):
            logging.debug(f"Processing submission: {json.dumps(submission, indent=2)}")
            problem_data = submission.get('problem', {})
            title = problem_data.get('problem_title', 'Untitled Image')
            image_filename = problem_data.get('problem_image')

            if image_filename:
                submission_id = submission.get('__id')
                image_endpoint = f'v1/projects/2/forms/report_problem/submissions/{submission_id}/attachments/{image_filename}'
                logging.debug(f"Constructed image endpoint: {image_endpoint} for submission {submission_id}")
                try:
                    image_data = self.download_image(image_endpoint)
                    processed_images[submission_id] = {
                        'submission_id': submission_id,
                        'title': title,
                        'label': problem_data.get('problem_label', None),
                        'image_data': image_data
                    }
                    logging.debug(f"Processed image for submission {submission_id}: {image_filename}")
                except Exception as e:
                    logging.error(f"Failed to download image for submission {submission_id}: {str(e)}")
                    logging.error(traceback.format_exc())
            else:
                logging.warning(f"No image data found in submission {submission.get('__id')}.")
        return processed_images

    def save_images(self, processed_images):
        logging.info("Saving images to the database.")
        for submission_id, image_info in processed_images.items():
            try:
                insert_image(
                    submission_id=image_info['submission_id'],
                    title=image_info['title'],
                    label=image_info.get('label', None),
                    image_data=image_info['image_data']
                )
                logging.info(f"Image '{image_info['title']}' saved for submission {submission_id}.")
            except Exception as e:
                logging.error(f"Failed to save image for submission {submission_id}: {str(e)}")
                logging.error(traceback.format_exc())

    def download_image(self, image_endpoint):
        headers = {
            "Authorization": f"Bearer {self.session_token}",
        }
        if image_endpoint.startswith('http://') or image_endpoint.startswith('https://'):
            image_url = image_endpoint
        else:
            image_url = urljoin(self.base_url + '/', image_endpoint.lstrip('/'))

        try:
            logging.debug(f"Downloading image from URL: {image_url}")
            response = requests.get(image_url, headers=headers)
            logging.debug(f"Image download response status code: {response.status_code}")
            response.raise_for_status()
            logging.info("Image downloaded successfully.")
            return response.content
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download image from {image_url}: {str(e)}")
            logging.error(traceback.format_exc())
            raise

    def update_existing_issues_and_responses(self):
        logging.info("Updating existing issues, images, and responses.")
        try:
            new_or_updated_issues = self.get_new_issues()
            images = self.get_images()
            self.fetch_responses()
            logging.info(f"Updated issues: {len(new_or_updated_issues)}, Images: {len(images)}")
            return {
                'issues': new_or_updated_issues,
                'images': images
            }
        except Exception as e:
            logging.error(f"Failed to update existing issues, images, and responses: {str(e)}")
            logging.error(traceback.format_exc())
            return {}

    def _format_date(self, date_string):
        if not date_string:
            logging.warning("Empty date string received.")
            return "1970-01-01 00:00:00"
        try:
            dt = datetime.fromisoformat(date_string.rstrip('Z'))
            formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            return formatted_date
        except ValueError as e:
            logging.error(f"Error formatting date '{date_string}': {str(e)}")
            return "1970-01-01 00:00:00"

if __name__ == "__main__":
    try:
        init_db()
        logging.info("Database initialized successfully with 'issues', 'images', and 'responses' tables.")
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        logging.error(traceback.format_exc())

    try:
        api = ODKAPI()
        result = api.update_existing_issues_and_responses()
        logging.info(f"Updated {len(result.get('issues', []))} issues and {len(result.get('images', []))} images.")
    except Exception as e:
        logging.error(f"Failed to update issues, images, and responses: {str(e)}")
        logging.error(traceback.format_exc())

    logging.info("Issues, images, and responses updating process completed.")
