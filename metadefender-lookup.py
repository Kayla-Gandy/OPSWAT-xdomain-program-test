import sys
import requests
import json
from os import path


def scan_file(file_path, API_key):
    if(not path.exists(file_path)):
        raise OSError("File provided does not exist.")
    
    file_to_upload = open(file_path, 'rb')
    files = {'file': (file_path, file_to_upload)}
    header = {'apikey': API_key, 'filename': path.basename(file_path)}
    scan_response = requests.post("https://api.metadefender.com/v4/file", files=files, headers=header)
    print(scan_response.text)

if __name__ == "__main__":
    if(len(sys.argv) != 2):
        raise OSError("File path not provided.")
    with open("keys.json", "r") as key_file:
        APIKey = json.load(key_file)["Meta_Cloud_Key"]
    scan_file(sys.argv[1], APIKey)
