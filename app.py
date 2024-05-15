import hashlib
import os
import shutil
import threading
import time
import uuid

from PIL import Image
from flask import Flask, flash, request, redirect, send_from_directory, render_template, send_file, url_for, \
    session
from werkzeug.utils import secure_filename

from lib.ProPainter.inference_propainter import inpaint
from util.MiVOS_util import MiVOS_Manager
from util.interactive_util import get_video_info, save_frames, array_to_bytesio, compose_mask, convert_to_mp4

UPLOAD_FOLDER = 'app/uploads'  # Folder where images should be saved to
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'gif', 'mpeg', 'mov', 'webm', 'flv'}

app = Flask(__name__, template_folder='app/template', static_folder='app/static')

SECRET_KEY = os.urandom(12)  # Set the secret key to a string of random symbols
app.secret_key = SECRET_KEY

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.add_url_rule('/app/uploads/<name>', endpoint='download_file', build_only=True)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size of 16 MB
manager_list = {}

SESSION_EXPIRATION_TIME = 3600  # Session expiration time in seconds
SESSION_CHECK_INTERVAL = 1800  # Check interval for expired sessions in seconds


# TODO: Use flashes
# TODO: Add progressbars in UI
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_etag(file_path):
    # Generate ETag based on the content of the file
    with open(file_path, 'rb') as f:
        file_content = f.read()
        etag = hashlib.md5(file_content).hexdigest()
        return etag


# Check and delete expired sessions
def check_expired_sessions():
    while True:
        current_time = time.time()
        with app.app_context():
            for session_id, created_time in list(session_expiration_times.items()):
                if current_time - created_time > SESSION_EXPIRATION_TIME:
                    # Session has expired, delete associated folder
                    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)
                    # Remove expired session from the dictionary
                    del session_expiration_times[session_id]
                    del manager_list[session_id]
                    print('Deleted ' + session_id)
        time.sleep(SESSION_CHECK_INTERVAL)


# Dictionary to store session creation times
session_expiration_times = {}

# Start the background thread for checking expired sessions
expired_session_checker = threading.Thread(target=check_expired_sessions)
expired_session_checker.daemon = True
expired_session_checker.start()


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
            session['video_uploaded'] = True
            video_name = secure_filename(file.filename)

            # Set up session
            session['session_id'] = str(uuid.uuid4())
            session_expiration_times[session['session_id']] = time.time()
            session['root_folder'] = os.path.join(app.config['UPLOAD_FOLDER'], session['session_id'])
            os.makedirs(session['root_folder'])

            # Save video
            file_path = os.path.join(session['root_folder'], video_name)
            file.save(file_path)

            mp4_video_name = convert_to_mp4(session['root_folder'], video_name)
            file_path = os.path.join(session['root_folder'], mp4_video_name)

            # Save frames
            frame_folder = os.path.join(session['root_folder'], 'frames')
            save_frames(file_path, frame_folder)
            session['num_frames'], session['fps'] = get_video_info(file_path)

            # Create mask folder and create an empty mask image
            mask_folder = os.path.join(session['root_folder'], 'masks')
            os.makedirs(mask_folder, exist_ok=True)
            temp_img = Image.open(os.path.join(frame_folder, '00000.png'))
            empty_img = Image.new("RGBA", temp_img.size, (0, 0, 0, 0))
            empty_img.save(os.path.join(session['root_folder'], 'empty.png'))

            manager_list[session['session_id']] = MiVOS_Manager(frame_folder)

            return redirect(url_for('mask_page'))
        else:
            flash('File extension not allowed')
    return render_template('index.html')


@app.route('/interactive')
def mask_page():
    if session.get('video_uploaded') and not session.get('video_inpainted'):
        return render_template('mask.html', num_frames=session.get('num_frames'), fps=session.get('fps'))
    return redirect(url_for('upload_file'))


@app.route('/result')
def result_page():
    if session.get('video_uploaded') and session.get('video_inpainted'):
        return render_template('result.html', num_frames=session.get('num_frames'), fps=session.get('fps'))
    return redirect(url_for('upload_file'))


@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route('/frame/<num>')
def get_frame(num):
    return send_from_directory(os.path.join(session['root_folder'], 'frames'), '{:05}.png'.format(int(num)))


@app.route('/mask/<num>')
def get_mask(num):
    mask_path = os.path.join(session['root_folder'], 'masks', '{:05}.png'.format(int(num)))
    if os.path.exists(mask_path):
        image_path = mask_path
    else:
        image_path = os.path.join(session['root_folder'], 'empty.png')

    # Generate ETag for the image file
    etag = generate_etag(image_path)

    # Check if client's ETag matches the current ETag
    match = request.headers.get('If-None-Match')
    if match is not None and match.strip('"') == etag:
        return 'Not modified', 304
    return send_file(image_path, etag=etag)


@app.route('/reset_interaction', methods=['POST'])
def reset_interaction():
    manager_list[session['session_id']].reset_this_interaction()
    return 'Reset interaction', 200


@app.route('/reset', methods=['POST'])
def reset():
    manager_list[session['session_id']].on_reset()
    image_path = os.path.join(session['root_folder'], 'empty.png')

    # Generate ETag for the image file
    etag = generate_etag(image_path)

    # Check if client's ETag matches the current ETag
    match = request.headers.get('If-None-Match')
    if match is not None and match.strip('"') == etag:
        return 'Not modified', 304
    return send_file(image_path, etag=etag)


@app.route('/undo', methods=['POST'])
def undo():
    data = request.get_json()
    mask = manager_list[session['session_id']].on_undo()

    mask_folder = os.path.join(session['root_folder'], 'masks')
    mask = compose_mask(mask)

    img = Image.fromarray(mask)
    img.save(os.path.join(mask_folder, '{:05d}.png'.format(data['frame_num'])))

    # Send current mask for instant feedback
    mask_io = array_to_bytesio(mask)
    return send_file(mask_io, mimetype='image/png')


@app.route('/upload_canvas', methods=['POST'])
def s2m():
    data = request.get_json()
    drawing_points = [tuple(p) for p in data['points']]
    mask = manager_list[session['session_id']].on_drawn(drawing_points, data['frame_num'], int(data['k']))

    mask_folder = os.path.join(session['root_folder'], 'masks')
    mask = compose_mask(mask)

    img = Image.fromarray(mask)
    img.save(os.path.join(mask_folder, '{:05d}.png'.format(data['frame_num'])))

    # Return current mask for instant feedback
    mask_io = array_to_bytesio(mask)
    return send_file(mask_io, mimetype='image/png')


@app.route('/propagate', methods=['POST'])
def propagate():
    data = request.get_json()
    mask_list = manager_list[session['session_id']].on_run(data['frame_num'])

    mask_folder = os.path.join(session['root_folder'], 'masks')
    os.makedirs(mask_folder, exist_ok=True)

    for i in range(len(mask_list)):
        img = compose_mask(mask_list[i])
        img = Image.fromarray(img)
        img.save(os.path.join(mask_folder, '{:05d}.png'.format(i)))

    mask = mask_list[data['frame_num']]
    mask = compose_mask(mask)

    # Return current mask for instant feedback
    mask_io = array_to_bytesio(mask)
    return send_file(mask_io, mimetype='image/png')


@app.route('/inpaint', methods=['POST'])
def inpaint_video():
    inpaint(os.path.join(session['root_folder'], 'frames'),
            os.path.join(session['root_folder'], 'masks'),
            os.path.join(session['root_folder'], 'frames'),
            session.get('fps'))

    session['video_inpainted'] = True
    return redirect(url_for('result_page'))


@app.route('/again', methods=['POST'])
def inpaint_again():
    session['video_inpainted'] = False
    mask_folder = os.path.join(session['root_folder'], 'masks')
    frame_folder = os.path.join(session['root_folder'], 'frames')
    # Delete masks
    if os.path.exists(mask_folder):
        shutil.rmtree(mask_folder)
        os.makedirs(mask_folder, exist_ok=True)
    # initialise frame
    manager_list[session['session_id']] = MiVOS_Manager(frame_folder)
    return redirect(url_for('mask_page'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
