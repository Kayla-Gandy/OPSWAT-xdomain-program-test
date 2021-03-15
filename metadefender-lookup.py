"""
Scans a file against OPSWAT's metadefender API
Author: Kayla Gandy
3/9/21
"""

import sys
import requests
import json
from hashlib import sha1
from os import path


def hash_file(file_path):
    """
    Opens a file at file_path (previously checked for existence)
    Calculates and returns calculated hash value of file using sha1
    """
    full_hash = sha1()
    block_size = 512
    with open(file_path, 'rb') as file_to_hash:
        data_block = file_to_hash.read(block_size)
        while data_block:
            full_hash.update(data_block)
            data_block = file_to_hash.read(block_size)
    return full_hash.hexdigest()

def retrieve_hash(file_path, API_key):
    """
    GET request to metadefender hash search using caculated hash of file
    (file previously checked for existence)
    Raises requests.exceptions.HTTPError if request is unsuccessful
    Returns response to hash search as JSON
    """
    file_hash = hash_file(file_path)
    hash_search_url = "https://api.metadefender.com/v4/hash/" + file_hash
    header = {'apikey': API_key}
    search_response = requests.get(hash_search_url, headers=header)
    search_response_json = json.loads(search_response.text)
    if 'error' in search_response_json and search_response_json['error']['code'] != 404003:
        search_response.raise_for_status()
    return search_response_json

def upload_file(file_path, API_key):
    """
    POST request to metadefender file upload
    (file previously checked for existence)
    Raises requests.exceptions.HTTPError if request is unsuccessful
    Returns response as JSON
    """
    file_to_upload = open(file_path, 'rb')
    files = {'file': (file_path, file_to_upload)}
    header = {'apikey': API_key, 'filename': path.basename(file_path)}
    scan_response = requests.post("https://api.metadefender.com/v4/file", files=files, headers=header)
    scan_response.raise_for_status()
    scan_response_json = json.loads(scan_response.text)
    return scan_response_json

def retrieve_by_id(data_id, API_key):
    """
    GET request to metadefender data ID search
    Raises requests.exceptions.HTTPError if request is unsuccessful
    Returns response to hash search as JSON
    """
    id_retreival_url = "https://api.metadefender.com/v4/file/" + data_id
    header = {'apikey': API_key}
    retrieve_response = requests.get(id_retreival_url, headers=header)
    retrieve_response.raise_for_status()
    retrieve_response_json = json.loads(retrieve_response.text)
    while "scan_results" not in retrieve_response_json or \
            retrieve_response_json['scan_results']['progress_percentage'] != 100:
        retrieve_response = requests.get(id_retreival_url, headers=header)
        retrieve_response.raise_for_status()
        retrieve_response_json = json.loads(retrieve_response.text)
    return retrieve_response_json

def print_data(response_json):
    """Prints JSON data from request"""
    results = response_json['scan_results']
    print("filename: " + response_json['file_info']['display_name'])
    print("overall_status: " + results['scan_all_result_a'])
    result_details = results['scan_details']
    for engine_name, engine_values in result_details.items():
        print("\nengine: " + engine_name)
        [print(str(key) + ": " + str(val)) for key, val in engine_values.items() if key != 'scan_time']

def scan_file(file_path, API_key):
    """
    Main function to scan against metadefender API
    Raises OSError if file does not exist
    Catches all request exceptions (requests.exceptions.HTTPError) and prints error
    """
    real_filepath = path.realpath(file_path)
    if not path.exists(real_filepath):
        raise OSError("File provided does not exist.")
    try:
        search_response_json = retrieve_hash(real_filepath, API_key)
        if 'error' in search_response_json:
            upload_response_json = upload_file(real_filepath, API_key)
            data_id = upload_response_json['data_id']
            search_response_json = retrieve_by_id(data_id, API_key)
        print_data(search_response_json)
    except requests.exceptions.HTTPError as err:
        print("Scan request error:")
        print(err)
        return


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise OSError("File path not provided.")
    with open("keys.json", "r") as key_file:
        APIKey = json.load(key_file)["Meta_Cloud_Key"]
    if not APIKey:
        raise OSError("API key not provided in file \'keys.json\'.")
    scan_file(sys.argv[1], APIKey)
