import base64
import os
import shutil
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from flask import Flask, flash, request, redirect, send_from_directory, render_template, jsonify, send_file, abort, \
    url_for, session
from werkzeug.utils import secure_filename

from util.interactive_util import save_frames, get_video_info, resize_image_to_frame
from util.propagation_util import propagate_all
from util.scribble_util import comp_image, MyManager

UPLOAD_FOLDER = 'app/uploads'  # Folder where images should be saved to
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'gif', 'mpeg', 'mov', 'webm', 'flv'}

app = Flask(__name__, template_folder='app/template', static_folder='app/static')

SECRET_KEY = os.urandom(12)  # Set the secret key to a string of random symbols
app.secret_key = SECRET_KEY

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.add_url_rule('/app/uploads/<name>', endpoint='download_file', build_only=True)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size of 16 MB

s2m_manager = MyManager()

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


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
            clear_folder(app.config['UPLOAD_FOLDER'])
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # Saving every frame
            save_frames(file_path, os.path.join(app.config['UPLOAD_FOLDER'], 'frames'))

            return redirect(url_for('mask_page', video_name=filename))
        else:
            flash('File extension not allowed')
    return render_template('index.html')


@app.route('/inpaint/<video_name>')
def mask_page(video_name):
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_name)
    num_frames, fps = get_video_info(video_path)
    return render_template('mask.html', num_frames=num_frames, fps=fps)


@app.route('/save_mask', methods=['POST'])
def save_mask():
    data = request.get_json()
    if 'image_data' in data:
        image_data = data['image_data']
        # Remove the prefix 'data:image/png;base64,' from the base64 encoded string
        image_data = image_data.replace('data:image/png;base64,', '')
        # Decode the base64 string to bytes
        image_bytes = base64.b64decode(image_data)

        # Get the frame the mask was drawn on
        current_frame = int(data['current_frame'])

        # Resize mask to match the frame
        frame_path = os.path.join(app.config["UPLOAD_FOLDER"], 'frames', '{:05}.png'.format(current_frame))
        image = Image.open(BytesIO(image_bytes)).convert('L')
        image = resize_image_to_frame(image, frame_path)
        image_array = np.array(image)

        # Save image as an array with 1 where the scribble is
        p_srb = np.where(image_array > 0, 1, 0)

        masks_folder = os.path.join(app.config["UPLOAD_FOLDER"], 'masks')
        os.makedirs(masks_folder, exist_ok=True)
        mask_path = os.path.join(masks_folder, '{:05}.png'.format(current_frame))

        # Scribble to mask
        s2m_manager.setup_manager(frame_path, mask_path)
        np_mask = s2m_manager.run_s2m(p_srb)

        # Save the mask
        cv2.imwrite(mask_path, np_mask)

        # Compose mask to display
        comp = comp_image(mask_path)

        return send_file(comp, mimetype='image/png')
    else:
        return jsonify({'error': 'No image data found.'}), 400


@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route('/frame/<num>')
def get_frame(num):
    return send_from_directory(os.path.join(app.config["UPLOAD_FOLDER"], 'frames'), '{:05}.png'.format(int(num)))


@app.route('/mask/<num>')
def get_mask(num):
    # Check if the image exists
    mask_path = os.path.join(app.config["UPLOAD_FOLDER"], 'masks', '{:05}.png'.format(int(num)))
    propagated_mask_path = os.path.join(app.config["UPLOAD_FOLDER"], 'propagated_masks', '{:05}.png'.format(int(num)))

    if os.path.exists(mask_path):
        image_path = mask_path
    elif os.path.exists(propagated_mask_path):
        image_path = propagated_mask_path
    else:
        return jsonify({'error': 'No image data found.'}), 204

    comp = comp_image(image_path)
    return send_file(comp, mimetype='image/png')


is_propagating = False


@app.route('/propagate')
def propagate():
    global is_propagating
    if not is_propagating:
        is_propagating = True
        propagate_all(os.path.join(app.config["UPLOAD_FOLDER"], 'frames'),
                      os.path.join(app.config["UPLOAD_FOLDER"], 'masks'),
                      os.path.join(app.config["UPLOAD_FOLDER"], 'propagated_masks'))
        is_propagating = False
    else:
        return 'Already propagating masks', 400, {'Content-Type': 'text/plain'}
    return 'Propagating masks', 200, {'Content-Type': 'text/plain'}


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
