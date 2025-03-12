import requests
import os
import sys
from urllib.parse import urlparse

def download_file(url, output_path=None):
    try:
        # Get filename from URL if output path is not specified
        if output_path is None:
            output_path = os.path.basename(urlparse(url).path)
        
        # Download the file
        response = requests.get(url)
        response.raise_for_status()
        
        # Save the file
        with open(output_path, 'wb') as file:
            file.write(response.content)
            
        print(f"File downloaded successfully to: {output_path}")
        
    except Exception as e:
        print(f"Error downloading file: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a download URL")
        sys.exit(1)
        
    url = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    download_file(url, output_path) 