import base64
import os
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template, jsonify
from moviepy.video.io.VideoFileClip import VideoFileClip
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'app/uploads'  # Folder where images should be saved to
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'gif', 'mpeg', 'mov', 'webm', 'flv'}

app = Flask(__name__, template_folder='app/template', static_folder='app/static')

SECRET_KEY = os.urandom(12)  # Set the secret key to a string of random symbols
app.secret_key = SECRET_KEY

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.add_url_rule('/app/uploads/<name>', endpoint='download_file', build_only=True)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size of 16 MB


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_to_mp4(folder_path, filename):
    """
    Converts a saved video file to mp4

    :param folder_path: Path from root to the folder where the video is saved
    :param filename: Name of the video file
    :return: The filename with a mp4 ending
    """
    file_path = os.path.join(folder_path, filename)
    video = VideoFileClip(file_path)

    output_filepath = file_path.split('.')[0] + ".mp4"
    video.write_videofile(output_filepath)

    os.remove(file_path)  # Delete original file
    print(file_path)
    mp4_filename = filename.split('.')[0] + ".mp4"
    return mp4_filename


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # Saving the uploaded file
            mp4_filename = convert_to_mp4(app.config['UPLOAD_FOLDER'], filename)
            file_url = url_for("get_file", filename=mp4_filename)
            return render_template('mask.html', file_url=file_url)
        else:
            flash('File extension not allowed')
    return render_template('index.html')


@app.route('/save_image', methods=['POST'])
def save_image():
    data = request.get_json()
    if 'image_data' in data:
        image_data = data['image_data']
        # Remove the prefix 'data:image/png;base64,' from the base64 encoded string
        image_data = image_data.replace('data:image/png;base64,', '')
        # Decode the base64 string to bytes
        image_bytes = base64.b64decode(image_data)
        # Save the image to a file
        with open(os.path.join(app.config['UPLOAD_FOLDER'], 'generated_mask.png'), 'wb') as f:
            f.write(image_bytes)
        return jsonify({'message': 'Image saved successfully.'}), 200
    else:
        return jsonify({'error': 'No image data found.'}), 400


@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == '__main__':
    app.run()
