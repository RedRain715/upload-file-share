from flask import Flask, render_template, request, send_file, abort
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Store file metadata
FILES_DB = 'files.json'

def load_files_db():
    if os.path.exists(FILES_DB):
        with open(FILES_DB, 'r') as f:
            return json.load(f)
    return {}

def save_files_db(db):
    with open(FILES_DB, 'w') as f:
        json.dump(db, f)

@app.route('/')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400

    # Generate unique filename
    filename = secure_filename(file.filename)
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(filename)[1]
    stored_filename = f"{file_id}{extension}"
    
    # Save the file
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], stored_filename))
    
    # Calculate expiration time
    hours = int(request.form.get('expiration', '24'))
    expiration_time = datetime.now() + timedelta(hours=hours)
    
    # Save file metadata
    files_db = load_files_db()
    files_db[file_id] = {
        'original_name': filename,
        'stored_name': stored_filename,
        'expiration': expiration_time.isoformat()
    }
    save_files_db(files_db)
    
    # Generate download link
    download_link = request.host_url + f'download/{file_id}'
    return f'Your file is available at: <a href="{download_link}">{download_link}</a>'

@app.route('/download/<file_id>')
def download_file(file_id):
    files_db = load_files_db()
    
    if file_id not in files_db:
        abort(404)
    
    file_info = files_db[file_id]
    expiration_time = datetime.fromisoformat(file_info['expiration'])
    
    if datetime.now() > expiration_time:
        # Remove expired file
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file_info['stored_name']))
        except:
            pass
        del files_db[file_id]
        save_files_db(files_db)
        return 'File has expired', 410
    
    return send_file(
        os.path.join(app.config['UPLOAD_FOLDER'], file_info['stored_name']),
        download_name=file_info['original_name']
    )

if __name__ == '__main__':
    app.run(debug=True) 