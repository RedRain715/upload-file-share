from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from github import Github
import base64
from pathlib import Path
import tempfile
import requests
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for flash messages

# GitHub configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = "upload-file-share"
USERNAME = "RedRain715"

# File configuration
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class GitHubFileSharer:
    def __init__(self):
        if not GITHUB_TOKEN:
            raise ValueError("GitHub token not found. Please set GITHUB_TOKEN environment variable.")
        self.github = Github(GITHUB_TOKEN)
        self.repo = self.github.get_user().get_repo(REPO_NAME)
        self.username = USERNAME

    def upload_file(self, file):
        try:
            # Secure the filename
            filename = secure_filename(file.filename)
            
            # Check file size
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            
            if size > MAX_FILE_SIZE:
                return None, "File size too large. Maximum size is 50MB."
            
            # Read and encode file content
            content = file.read()
            encoded_content = base64.b64encode(content).decode()
            
            try:
                # Try to get existing file
                contents = self.repo.get_contents(filename)
                self.repo.update_file(
                    contents.path,
                    f"Update {filename}",
                    encoded_content,
                    contents.sha
                )
                status = "updated"
            except:
                # File doesn't exist, create new one
                self.repo.create_file(
                    filename,
                    f"Upload {filename}",
                    encoded_content
                )
                status = "uploaded"
            
            # Generate download link
            download_url = f"https://raw.githubusercontent.com/{self.username}/{self.repo.name}/main/{filename}"
            return download_url, f"File successfully {status}!"
            
        except Exception as e:
            return None, f"Error uploading file: {str(e)}"

    def get_all_files(self):
        try:
            contents = self.repo.get_contents("")
            files = []
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(self.repo.get_contents(file_content.path))
                else:
                    download_url = f"https://raw.githubusercontent.com/{self.username}/{self.repo.name}/main/{file_content.path}"
                    # Get file size in MB
                    size_mb = round(file_content.size / 1024 / 1024, 2)
                    # Get last modified time
                    last_modified = file_content.last_modified
                    
                    files.append({
                        'name': file_content.path,
                        'download_url': download_url,
                        'size': size_mb,
                        'last_modified': last_modified
                    })
            return files, None
        except Exception as e:
            return [], f"Error getting files: {str(e)}"

@app.route('/')
def index():
    try:
        sharer = GitHubFileSharer()
        files, error = sharer.get_all_files()
        if error:
            flash(error, 'error')
        return render_template('index.html', files=files)
    except Exception as e:
        flash(str(e), 'error')
        return render_template('index.html', files=[])

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash(f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}', 'error')
        return redirect(url_for('index'))
    
    try:
        sharer = GitHubFileSharer()
        download_url, message = sharer.upload_file(file)
        
        if download_url:
            flash(message, 'success')
        else:
            flash(message, 'error')
            
    except Exception as e:
        flash(f'Upload failed: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.errorhandler(Exception)
def handle_error(error):
    flash(f"An error occurred: {str(error)}", 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 