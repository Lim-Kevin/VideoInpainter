import base64
import os
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from flask import Flask, flash, request, redirect, send_from_directory, render_template, jsonify, send_file
from werkzeug.utils import secure_filename

from util.interactive_util import save_frames, get_video_info, resize_image_to_frame
from util.scribble_util import setup_manager, comp_image

UPLOAD_FOLDER = 'app/uploads'  # Folder where images should be saved to
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'gif', 'mpeg', 'mov', 'webm', 'flv'}

app = Flask(__name__, template_folder='app/template', static_folder='app/static')

SECRET_KEY = os.urandom(12)  # Set the secret key to a string of random symbols
app.secret_key = SECRET_KEY

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # TODO: Maybe clear upload folder everytime before uploading new file

app.add_url_rule('/app/uploads/<name>', endpoint='download_file', build_only=True)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size of 16 MB


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            save_frames(file_path, os.path.join(app.config['UPLOAD_FOLDER'], 'frames'))
            num_frames, fps = get_video_info(file_path)
            return render_template('mask.html', num_frames=num_frames, fps=fps)
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

        # Get the frame the mask was drawn on
        current_frame = int(data['current_frame'])
        frame_path = os.path.join(app.config["UPLOAD_FOLDER"], 'frames', 'frame%s.png' % current_frame)

        image = Image.open(BytesIO(image_bytes)).convert('L')
        image = resize_image_to_frame(image, frame_path)

        image_array = np.array(image)
        p_srb = np.where(image_array > 0, 1, 0)  # Save image as an array with 1 where the scribble is

        manager = setup_manager(frame_path)
        np_mask = manager.run_s2m(p_srb)
        # TODO: Display mask instead of just saving it
        cv2.imwrite(os.path.join(app.config["UPLOAD_FOLDER"], 'mask.png'), np_mask)

        output = BytesIO()
        temp = Image.fromarray(comp_image(np_mask))
        temp.save(output, format='PNG')
        output.seek(0)

        return send_file(output, mimetype='image/png')
    else:
        return jsonify({'error': 'No image data found.'}), 400


@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route('/frame/<num>')
def get_frame(num):
    return send_from_directory(os.path.join(app.config["UPLOAD_FOLDER"], 'frames'), 'frame%s.png' % num)


if __name__ == '__main__':
    app.run()
