import os
import sys
import requests
from github import Github
import base64
from pathlib import Path
import json

class GitHubFileSharer:
    def __init__(self, github_token, repo_name):
        self.github = Github(github_token)
        self.repo = self.github.get_user().get_repo(repo_name)
        self.username = "RedRain715"  # Add your username
        
    def upload_file(self, file_path):
        try:
            # Read file content
            with open(file_path, 'rb') as file:
                content = file.read()
            
            # Create file in GitHub
            file_name = os.path.basename(file_path)
            encoded_content = base64.b64encode(content).decode()
            
            try:
                # Try to get existing file
                contents = self.repo.get_contents(file_name)
                self.repo.update_file(
                    contents.path,
                    f"Update {file_name}",
                    encoded_content,
                    contents.sha
                )
            except:
                # File doesn't exist, create new one
                self.repo.create_file(
                    file_name,
                    f"Upload {file_name}",
                    encoded_content
                )
            
            # Generate download link
            download_url = f"https://raw.githubusercontent.com/{self.username}/{self.repo.name}/main/{file_name}"
            return download_url
            
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return None

    def upload_folder(self, folder_path):
        try:
            links = {}
            folder_path = Path(folder_path)
            
            # Walk through the folder
            for file_path in folder_path.rglob('*'):
                if file_path.is_file():
                    # Get relative path from the root folder
                    relative_path = str(file_path.relative_to(folder_path))
                    
                    # Read and upload file
                    with open(file_path, 'rb') as file:
                        content = file.read()
                    
                    encoded_content = base64.b64encode(content).decode()
                    
                    try:
                        # Try to get existing file
                        contents = self.repo.get_contents(relative_path)
                        self.repo.update_file(
                            contents.path,
                            f"Update {relative_path}",
                            encoded_content,
                            contents.sha
                        )
                    except:
                        # File doesn't exist, create new one
                        self.repo.create_file(
                            relative_path,
                            f"Upload {relative_path}",
                            encoded_content
                        )
                    
                    # Generate download link
                    download_url = f"https://raw.githubusercontent.com/{self.username}/{self.repo.name}/main/{relative_path}"
                    links[relative_path] = download_url
            
            return links
            
        except Exception as e:
            print(f"Error uploading folder: {str(e)}")
            return None

if __name__ == "__main__":
    # Get token from environment variable for security
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    if not GITHUB_TOKEN:
        print("Please set your GITHUB_TOKEN environment variable")
        sys.exit(1)
        
    REPO_NAME = "upload-file-share"
    
    sharer = GitHubFileSharer(GITHUB_TOKEN, REPO_NAME)
    
    if len(sys.argv) < 2:
        print("Please provide a file or folder path")
        sys.exit(1)
        
    path = sys.argv[1]
    
    if os.path.isfile(path):
        link = sharer.upload_file(path)
        if link:
            print(f"Download link: {link}")
    elif os.path.isdir(path):
        links = sharer.upload_folder(path)
        if links:
            print("Download links:")
            for file_path, link in links.items():
                print(f"{file_path}: {link}") 