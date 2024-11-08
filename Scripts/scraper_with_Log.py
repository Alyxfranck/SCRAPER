import requests
import json
import logging
import time
from datetime import datetime, timezone

# Set up logging
logging.basicConfig(filename='scraper_log.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
SUBMIT_URL = "http://localhost/api/submit-scrape-job"
STATUS_URL_TEMPLATE = "http://localhost/api/job/{}"
AUTH_URL = "http://localhost/api/auth/token"  # Adjusted to the correct authentication endpoint
MAX_RETRIES = 3
RETRY_DELAY = 2

# Variables
output_data = []
token = None

# Function to authenticate and retrieve the access token
def authenticate():
    global token
    try:
        response = requests.post(AUTH_URL, data={"username": "your_username", "password": "your_password"})
        response.raise_for_status()
        token_data = response.json()
        token = token_data.get("access_token")
        if token:
            logging.info("Successfully retrieved access token.")
        else:
            logging.error("Failed to retrieve access token.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Authentication failed: {e}")

# Function to submit a scraping job
def submit_scraping_job(url_to_scrape):
    headers = {"Authorization": f"Bearer {token}"}
    job_data = {
        "id": "",
        "url": url_to_scrape,
        "elements": [
            {
                "name": "ContactSection",
                "xpath": '//section[@id="contact" and contains(@class, "flex") and contains(@class, "flex-col")]',
                "url": url_to_scrape
            }
        ],
        "user": "",
        "time_created": datetime.now(timezone.utc).isoformat(),
        "result": [],
        "job_options": {
            "multi_page_scrape": False,
            "custom_headers": {}
        },
        "status": "Queued",
        "chat": ""
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(SUBMIT_URL, json=job_data, headers=headers)
            response.raise_for_status()
            job_id = response.json().get("id")
            
            if job_id:
                logging.info(f"Successfully submitted job for {url_to_scrape}, Job ID: {job_id}")
                return job_id
            else:
                logging.error(f"No job ID returned in response for {url_to_scrape}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to submit job for {url_to_scrape} on attempt {attempt + 1}/{MAX_RETRIES}: {e}")
        
        time.sleep(RETRY_DELAY)
    
    logging.error(f"Could not submit job for {url_to_scrape} after {MAX_RETRIES} attempts.")
    return None

# Function to check the status of a job with added verification for list response
def check_job_status(job_id):
    headers = {"Authorization": f"Bearer {token}"}
    status_url = STATUS_URL_TEMPLATE.format(job_id)
    
    while True:
        try:
            response = requests.get(status_url, headers=headers)
            response.raise_for_status()
            job_info = response.json()
            logging.debug(f"Job info for ID {job_id}: {job_info}")

            # Check if job_info is a dictionary or list
            if isinstance(job_info, list):
                logging.error(f"Received a list instead of expected dictionary for Job ID {job_id}. Attempting to parse.")
                # Attempt to extract status from the first item if list has elements
                if job_info and isinstance(job_info[0], dict):
                    job_status = job_info[0].get("status")
                    result = job_info[0].get("result", [])
                else:
                    logging.warning(f"Unable to extract status information from list response for Job ID {job_id}")
                    return None
            elif isinstance(job_info, dict):
                job_status = job_info.get("status")
                result = job_info.get("result", [])
            else:
                logging.error(f"Unexpected format for Job ID {job_id}: {type(job_info)}")
                return None
            
            # Check job status and return results if completed
            if job_status == "Completed":
                logging.info(f"Job ID {job_id} completed.")
                return result
            elif job_status == "Failed":
                logging.error(f"Job ID {job_id} failed.")
                return None
            else:
                logging.info(f"Job ID {job_id} is still in progress. Retrying...")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to check status for Job ID {job_id}: {e}")
        
        time.sleep(RETRY_DELAY)

def process_result(result, url):
    contact_text = "No text available"
    if result:
        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    # Match URL keys regardless of trailing slash
                    for key in item.keys():
                        if key.rstrip('/') == url.rstrip('/'):
                            url_data = item[key]
                            contact_section_data = url_data.get("ContactSection", [])
                            if contact_section_data:
                                first_element = contact_section_data[0]
                                if isinstance(first_element, dict):
                                    contact_text = first_element.get("text", "No text available")
                                elif isinstance(first_element, str):
                                    contact_text = first_element
                                else:
                                    logging.warning(f"Unexpected data type for first_element: {type(first_element)}")
                            else:
                                logging.warning(f"No 'ContactSection' data found for {url}")
                            break
        elif isinstance(result, dict):
            contact_section = result.get("ContactSection", [])
            if contact_section:
                first_element = contact_section[0]
                if isinstance(first_element, dict):
                    contact_text = first_element.get("text", "No text available")
                elif isinstance(first_element, str):
                    contact_text = first_element
                else:
                    logging.warning(f"Unexpected data type for first_element: {type(first_element)}")
            else:
                logging.warning(f"No 'ContactSection' data found for {url}")
    else:
        logging.warning(f"No contact info found for {url}")

    # Append to output_data
    contact_info = {
        "url": url,
        "contact": contact_text
    }
    output_data.append(contact_info)
    logging.info(f"Contact info saved for {url}")

# Main execution logic
try:
    authenticate()  # Obtain the access token at the start

    # Load URLs from the JSON file
    url_file_path = 'urls.json'
    with open(url_file_path, 'r', encoding='utf-8') as file:
        urls = json.load(file)
    
    # Process each URL
    for url in urls:
        job_id = submit_scraping_job(url)
        
        if job_id:
            result = check_job_status(job_id)
            logging.debug(f"Scraped result for url: {url}, result: {result}")
            process_result(result, url)
            time.sleep(RETRY_DELAY)  # Short delay between jobs
        else:
            logging.error(f"Skipping job for {url} due to submission failure.")

finally:
    # Save the extracted data to a JSON file
    with open("contact_data.json", "w", encoding='utf-8') as outfile:
        json.dump(output_data, outfile, indent=4, ensure_ascii=False)
    logging.info("Scraping complete, data saved to contact_data.json")
