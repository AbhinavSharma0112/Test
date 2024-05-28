from flask import Flask, jsonify, request, redirect, session, url_for, render_template
from flask_restful import Api, Resource, reqparse
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import yaml
import os
import base64
import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import time
import traceback

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session
api = Api(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_client = MongoClient('mongodb://77.37.45.154:27017/')
db = mongo_client['UserAuth']
users_collection = db['Users']

# Example database for storing user data
users = [
    {'username': 'user1', 'password_hash': generate_password_hash('password1')},
    {'username': 'user2', 'password_hash': generate_password_hash('password2')}
]

# Parser for parsing login/signup requests
parser = reqparse.RequestParser()
parser.add_argument('username', type=str, required=True, help="Username is required")
parser.add_argument('password', type=str, required=True, help="Password is required")


class Login(Resource):
    def post(self):
        args = parser.parse_args()
        username = args['username']
        password = args['password']

        # Check if user exists
        user = next((u for u in users if u['username'] == username), None)
        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username  # Log in the user
            return {'message': 'Login successful'}, 200
        else:
            return {'error': 'Invalid username or password'}, 401


class Signup(Resource):
    def post(self):
        args = parser.parse_args()
        username = args['username']
        password = args['password']

        # Check if username is already taken
        if users_collection.find_one({'username': username}):
            return {'error': 'Username already exists'}, 400

        # Hash the password
        password_hash = generate_password_hash(password)

        # Insert new user data into MongoDB
        user_data = {'username': username, 'password': password_hash}
        users_collection.insert_one(user_data)

        return {'message': 'Signup successful'}, 201


# Add resources to the API
# api.add_resource(Login, '/login')
# api.add_resource(Signup, '/signup')


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_client = MongoClient('mongodb://77.37.45.154:27017/')
db = mongo_client['UserAuth']
users_collection = db['Users']

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")

ip_request_counts = {}


def update_ip_request_count(ip_address):
    logger.info(f"Updating request count for IP address: {ip_address}")
    current_time = time.time()
    if ip_address in ip_request_counts:
        count, timestamp = ip_request_counts[ip_address]
        if current_time - timestamp > 3600:  # Reset count if more than 1 hour has passed
            ip_request_counts[ip_address] = (1, current_time)
        else:
            ip_request_counts[ip_address] = (count + 1, timestamp)
    else:
        ip_request_counts[ip_address] = (1, current_time)

    # Check if the IP has exceeded the limit (e.g., 100 requests per hour)
    if ip_request_counts[ip_address][0] > 10:
        return False
    else:
        return True


def check_rate_limit(response):
    logger.info("Checking rate limit")
    if 'headers' in response:
        remaining = int(response['headers'].get('X-RateLimit-Remaining', 0))
        reset_time = int(response['headers'].get('X-RateLimit-Reset', 0))
        return remaining, reset_time
    else:
        # If response does not contain headers, return default values
        return 0, 0


def delete_file_from_github(company_name, repo_name, file_name, github_token):
    logger.info(f"Deleting file '{file_name}' from GitHub")
    file_path = f'Pipeline/SoftwareMathematics/{company_name}/{repo_name}/{file_name}'
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}'

    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    # Fetch the file's current content and SHA hash
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for non-200 status codes

        file_data = response.json()
        sha = file_data.get('sha')

        # Prepare the deletion request payload
        payload = {
            'message': 'Delete file',  # Provide a descriptive message for the deletion
            'sha': sha  # Include the SHA hash of the file's current content
        }

        response = requests.delete(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for non-200 status codes

        if response.status_code == 200:
            logger.info(f"File '{file_path}' deleted successfully from the GitHub repository.")
        else:
            logger.error(
                f"Failed to delete file '{file_path}' from the GitHub repository. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while deleting file '{file_path}': {e}")
        return False

    return True


def fetch_file_names(company_name, repo_name, access_token):
    logger.info(f"Fetching file names for company '{company_name}' and repo '{repo_name}'")
    file_names = []

    target_url = (
        f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/Pipeline/SoftwareMathematics/'
        f'{company_name}/{repo_name}')
    headers = {"Authorization": f"token {access_token}"} if access_token else {}

    response = requests.get(target_url, headers=headers)

    if response.status_code != 200:
        logger.error(f"Failed to fetch Files. Status code: {response.status_code}")
        return file_names

    for item in response.json():
        if item["type"] == "file":
            file_names.append(item["name"])

    return file_names


def fetch_repo_names(company_name, access_token):
    logger.info(f"Fetching repository names for company '{company_name}'")
    repo_names = []

    target_url = (
        f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/Pipeline/SoftwareMathematics/'
        f'{company_name}')

    headers = {"Authorization": f"token {access_token}"} if access_token else {}

    response = requests.get(target_url, headers=headers)

    if response.status_code != 200:
        logger.error(f"Failed to fetch repositories. Status code: {response.status_code}")
        return repo_names

    for item in response.json():
        if item["type"] == "dir":
            repo_names.append(item["name"])

    return repo_names


def get_company_names(repo_owner, repo_name, github_token):
    company_names = []

    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/Pipeline/SoftwareMathematics'
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Parse the response JSON
        content = response.json()
        # Filter out directories
        directories = [item['name'] for item in content if item['type'] == 'dir']
        # Append directory names to company_names list
        company_names.extend(directories)
    else:
        logger.error(f"Failed to fetch company names. Status code: {response.status_code}")
        logger.error("Response content: %s", response.content.decode())  # Print response content for debugging

    return company_names


def get_company_details(company_name, repo_name, file_name, REPO_OWNER, REPO_NAME,
                        GITHUB_TOKEN):
    company_details = {}

    file_path = f'Pipeline/SoftwareMathematics/{company_name}/{repo_name}/{file_name}'
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}'

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:

        yaml_content = yaml.safe_load(base64.b64decode(response.json()['content']).decode())

        if yaml_content is not None:
            for key, value in yaml_content.items():

                if value is None:
                    yaml_content[key] = ""

                elif isinstance(value, str):
                    formatted_string = value.replace('-', '').split()
                    formatted_string_space = ' '.join(formatted_string)
                    yaml_content[key] = formatted_string_space

            company_details = yaml_content

        else:
            company_details = {}
    else:
        logger.error(f"Failed to fetch YAML content. Status code: {response.status_code}")
    return company_details


@app.route('/add', methods=['GET', 'POST'])
def add_form():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form.get('username')
        companyname = request.form.get('companyname')
        repo_url = request.form.get('repourl')
        enabled = request.form.get('enabled')
        job_type = request.form.get('job_type')
        run_command = request.form.get('runcmnd')
        src_path = request.form.get('srcpath')
        application_port = request.form.get('applicationport')
        deploy_port = request.form.get('deployport')
        ssh_port_prod = request.form.get('sshportprod')
        ssh_port_dev = request.form.get('sshportdev')
        build_command = request.form.get('buildcommand')
        pvt_deploy_servers_dev = request.form.get('pvtdeployserversdev')
        deploy_servers_dev = request.form.get('deployserversdev')
        pvt_deploy_servers_prod = request.form.get('pvtdeployserversprod')
        deploy_servers_prod = request.form.get('deployserversprod')
        deploy_env_prod = request.form.get('deployenvprod')
        deploy_env_dev = request.form.get('deployenvdev')
        deploy_env = request.form.get('deployenv')

        # Assuming pvt_deploy_servers_dev is a string containing IP addresses separated by spaces
        pvt_deploy_servers_dev_list = format_ip_list(pvt_deploy_servers_dev)
        deploy_servers_prod_list = format_ip_list(deploy_servers_prod)
        pvt_deploy_servers_prod_list = format_ip_list(pvt_deploy_servers_prod)
        deploy_servers_dev_list = format_ip_list(deploy_servers_dev)
        deploy_env_list = format_ip_list(deploy_env)

        # Define the order of fields
        field_order = [
            "name", "company_name", "repository url", "enabled", "job_type", "run_command",
            "src_path", "application_port", "deploy_port", "ssh_port_prod", "ssh_port_dev",
            "build_command", "pvt_deploy_servers_dev", "deploy_servers_dev",
            "pvt_deploy_servers_prod", "deploy_servers_prodt", "deploy_env_prod",
            "deploy_env_dev", "deploy_env"
        ]

        # Define the data
        data = {
            "name": username,
            "company_name": companyname,
            "repository url": repo_url,
            "enabled": enabled,
            "job_type": job_type,
            "run_command": run_command,
            "src_path": src_path,
            "application_port": application_port,
            "deploy_port": deploy_port,
            "ssh_port_prod": ssh_port_prod,
            "ssh_port_dev": ssh_port_dev,
            "build_command": build_command,
            "pvt_deploy_servers_dev": pvt_deploy_servers_dev_list,
            "deploy_servers_dev": deploy_servers_dev_list,
            "pvt_deploy_servers_prod": pvt_deploy_servers_prod_list,
            "deploy_servers_prod": deploy_servers_prod_list,
            "deploy_env_prod": deploy_env_prod,
            "deploy_env_dev": deploy_env_dev,
            "deploy_env": deploy_env_list
        }

        # Save to GitHub
        result_message = save_to_github(data)
        logger.info(result_message)

        return result_message

    return "Data saved successfully!!"


def format_ip_list(ip_string):
    if ip_string:
        return ' '.join(['-' + ip for ip in filter(None, ip_string.split())])
    else:
        return ''


@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == "GET":
        company_names = request.args.get('company_name')
        repo_names = request.args.get('repo_name')
        file_names = request.args.get('file_name')
        company_details = get_company_details(company_names, repo_names, file_names, REPO_OWNER, REPO_NAME,
                                              GITHUB_TOKEN)
        return render_template("update.html", company_details=company_details)

    elif request.method == "POST":
        try:
            # Extract data from the form
            new_data = {
                'name': request.form.get('username'),
                'company_name': request.form.get('companyname'),
                'enabled': request.form.get('enabled') == 'yes',  # Convert to boolean
                'job_type': request.form.get('job_type'),
                'repository url': request.form.get('repourl'),
                'run_command': request.form.get('runcmnd'),
                'src_path': request.form.get('srcpath'),
                'application_port': request.form.get('applicationport'),
                'deploy_port': request.form.get('deployport'),
                'ssh_port_prod': request.form.get('sshportprod'),
                'ssh_port_dev': request.form.get('sshportdev'),
                'build_command': request.form.get('buildcommand'),
                'pvt_deploy_servers_dev': format_ip_list(request.form.get('pvtdeployserversdev')),
                'deploy_servers_dev': format_ip_list(request.form.get('deployserversdev')),
                'pvt_deploy_servers_prod': format_ip_list(request.form.get('pvtdeployserversprod')),
                'deploy_servers_prod': format_ip_list(request.form.get('deployserversprod')),
                'deploy_env_prod': request.form.get('deployenvprod'),
                'deploy_env_dev': request.form.get('deployenvdev'),
                'deploy_env': request.form.get('deployenv')
            }

            # If old username is not None and is different from the new username
            new_username = request.form.get('username')
            old_username = request.form.get('old_username')
            company_name = request.form.get('companyname')

            repo_parts = new_data["repository url"].split('/')
            repo_name = repo_parts[-1]

            # If username or repository URL is changed
            if old_username != new_username:
                delete_file_from_github(company_name, repo_name, old_username + '.yaml', GITHUB_TOKEN)

                # Save the updated file to GitHub with the new username
                new_data['name'] = new_username
                save_to_github(new_data)
                logger.info("Updated")
                return "Updated"
            else:
                save_to_github(new_data)
                logger.info("Updated")
                return "Updated"

        except Exception as e:
            error_message = traceback.format_exc()  # Get the full traceback as a string
            logger.error(f"An error occurred: {error_message}")  # Log the error message
            return render_template("error.html", error_message=error_message)

    return "Updated"


def save_to_github(data,branch='Test2'):
    field_order = [
        "name", "company_name", "repository url", "enabled", "job_type", "run_command",
        "src_path", "application_port", "deploy_port", "ssh_port_prod", "ssh_port_dev",
        "build_command", "pvt_deploy_servers_dev", "deploy_servers_dev",
        "pvt_deploy_servers_prod", "deploy_servers_prodt", "deploy_env_prod",
        "deploy_env_dev", "deploy_env"
    ]

    # Format the data into YAML format
    formatted_yaml = ''
    for field in field_order:
        value = data.get(field, 'null')
        if isinstance(value, list):
            value = yaml.dump(value, default_flow_style=False).strip()
        formatted_yaml += f"{field}: {value}\n"

    # Encode YAML content to base64
    file_content_base64 = base64.b64encode(formatted_yaml.encode()).decode()

    # Construct the file path
    repo_parts = data["repository url"].split('/')
    repo_name = repo_parts[-1]
    file_name = f'{data["name"]}.yaml'
    file_path = f'Pipeline/SoftwareMathematics/{data["company_name"]}/{repo_name}/{file_name}'

    # Construct the GitHub API URL
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}'

    # Prepare headers for the GitHub API request
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Check if the file already exists on GitHub
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # File already exists, update its content
        existing_file = response.json()
        payload = {
            'message': 'Update file',
            'content': file_content_base64,
            'sha': existing_file['sha'],  # SHA of the existing file for update
            'Branch':branch
        }
        response = requests.put(url, headers=headers, json=payload)
    elif response.status_code == 404:
        # File does not exist, create a new file
        payload = {
            'message': 'Create file',
            'content': file_content_base64,
            'branch':branch
        }
        response = requests.put(url, headers=headers, json=payload)

    # Return the result message
    if response.status_code == 201 or response.status_code == 200:
        logger.info('File saved successfully to GitHub.')
        return 'File saved successfully to GitHub.'
    else:
        logger.error(f'Failed to save file to GitHub. Status code: {response.status_code}')
        return f'Failed to save file to GitHub. Status code: {response.status_code}'


@app.route('/create')
def create_user():
    try:
        return render_template("index.html")
    except Exception as e:
        logger.error(f"An error occurred in /create route: {str(e)}")
        return "An error occurred"


@app.route('/', methods=['GET', 'POST'])
def new_index():
    try:
        if 'username' not in session:
            # If user is not logged in, redirect to login page
            return redirect(url_for('login'))
        if request.method == 'POST':
            data = request.get_json()
            company_names = data.get('company_name')
            repo_names = data.get('repo_name')
            file_names = data.get('file_name')
            if company_names and not repo_names:
                repo_names = fetch_repo_names(company_names, GITHUB_TOKEN)
                return jsonify(repo_names)

            if company_names and repo_names:
                file_names = fetch_file_names(company_names, repo_names, GITHUB_TOKEN)
                return jsonify(file_names)
            else:
                return jsonify({})
        else:
            # Handle the GET request here
            company_names = get_company_names(REPO_OWNER, REPO_NAME, GITHUB_TOKEN)

            # Log company names
            logger.info(f"Company names: {company_names}")

            return render_template("base.html", company_names=company_names)
    except Exception as e:
        # Log any exceptions
        logger.error(f"An error occurred in / route: {str(e)}")
        return "An error occurred"


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            # Check if the username exists in the database
            user = users_collection.find_one({'username': username})
            if user and check_password_hash(user['password'], password):
                # If username and password match, log in the user
                session['username'] = username
                return redirect('/')
            else:
                # If username or password is incorrect, render the login page with an error
                return render_template('login.html', error='Invalid username or password')

        else:
            # If it's a GET request, render the login form
            return render_template('login.html')
    except Exception as e:
        # Log any exceptions
        logger.error(f"An error occurred in /login route: {str(e)}")
        return "An error occurred"


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    try:
        if request.method == 'POST':
            # Retrieve form data
            username = request.form.get('username')
            password = request.form.get('password')

            # Check if the username already exists
            if users_collection.find_one({'username': username}):
                error_message = 'Username already exists. Please choose a different username.'
                return render_template('sign_up.html', error=error_message)

            # Hash the password before storing it
            hashed_password = generate_password_hash(password)

            # Insert new user data into MongoDB
            user_data = {'username': username, 'password': hashed_password}
            users_collection.insert_one(user_data)

            return redirect(url_for('login'))
        else:
            return render_template('sign_up.html')
    except Exception as e:
        # Log any exceptions
        logger.error(f"An error occurred in /signup route: {str(e)}")
        return "An error occurred"


@app.route('/logout')
def logout():
    try:
        session.pop('username', None)  # Remove the username from the session
        return redirect(url_for('login'))
    except Exception as e:
        # Log any exceptions
        logger.error(f"An error occurred in /logout route: {str(e)}")
        return "An error occurred"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

