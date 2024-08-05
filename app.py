import hashlib
import os
import shutil
import uuid
from datetime import timedelta, datetime

import cv2
from PIL import Image
from flask import Flask, request, redirect, send_from_directory, render_template, send_file, url_for, \
    session
from werkzeug.utils import secure_filename

from lib.ProPainter.inference_propainter import inpaint
from util.MiVOS_util import MiVOS_Manager
from util.interactive_util import get_video_info, save_frames, array_to_bytesio, compose_mask, convert_to_mp4
from util.scribble_util import scale_points

UPLOAD_FOLDER = 'app/uploads'  # Folder where images should be saved to
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'gif', 'mpeg', 'mov', 'webm', 'flv'}

app = Flask(__name__, template_folder='app/template', static_folder='app/static')

SECRET_KEY = os.urandom(12)  # Set the secret key to a string of random symbols
app.secret_key = SECRET_KEY

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if os.path.exists(UPLOAD_FOLDER):
    shutil.rmtree(UPLOAD_FOLDER)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024  # Max file size of 6 MB
manager_list = {}

SESSION_EXPIRATION_TIME = timedelta(minutes=30)  # Set time the session should expire in


# TODO: Update Google Drive link in README.md

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_etag(file_path):
    # Generate ETag based on the content of the file
    with open(file_path, 'rb') as f:
        file_content = f.read()
        etag = hashlib.md5(file_content).hexdigest()
        return etag


@app.before_request
def check_session_expired():
    if 'session_id' in session and request.endpoint not in ('index', 'upload_file'):
        if datetime.utcnow().replace(tzinfo=None) - session['creation_time'].replace(
                tzinfo=None) > SESSION_EXPIRATION_TIME:
            # Session expired, delete the corresponding folder
            delete_session()
        else:
            # Renew session timeout
            session['creation_time'] = datetime.utcnow()


# Use this to trigger app.before_request
@app.route('/check', methods=['POST'])
def check():
    return '', 200


@app.route('/delete_session', methods=['POST'])
def delete_session():
    if session.get('root_folder'):
        print('Deleted session: ' + str(session['session_id']))
        shutil.rmtree(session['root_folder'])
        del manager_list[session['session_id']]
        session.clear()
    return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            # flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            # flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            session['video_uploaded'] = True
            video_name = secure_filename(file.filename)

            # Set up session
            session.permanent = True
            session['session_id'] = str(uuid.uuid4())
            session['creation_time'] = datetime.utcnow()
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
            return render_template('index.html', message='Failed to upload file')
    return redirect(url_for('index'))


@app.route('/interactive')
def mask_page():
    if session.get('video_uploaded'):
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


@app.errorhandler(413)
def request_entity_too_large(error):
    return render_template('index.html', message='File is too large, please submit a file smaller than 6 MB')


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
    if not os.path.exists(image_path):
        return 'Folder deleted', 404
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
    data = request.get_json()
    manager_list[session['session_id']].on_reset()

    # Delete mask file
    mask_path = os.path.join(session['root_folder'], 'masks', '{:05}.png'.format(int(data['frame_num'])))
    if os.path.exists(mask_path):
        os.remove(mask_path)

    empty_image = os.path.join(session['root_folder'], 'empty.png')

    # Generate ETag for the image file
    etag = generate_etag(empty_image)

    # Check if client's ETag matches the current ETag
    match = request.headers.get('If-None-Match')
    if match is not None and match.strip('"') == etag:
        return 'Not modified', 304
    return send_file(empty_image, etag=etag)


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


@app.route('/save_video', methods=['POST'])
def save_video():
    frame_folder = os.path.join(session['root_folder'], 'frames')
    frames = [f for f in os.listdir(frame_folder)]
    frames.sort()

    first_frame_path = os.path.join(frame_folder, frames[0])
    frame = cv2.imread(first_frame_path)
    height, width, layers = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_path = os.path.join(session['root_folder'], 'inpainted.mp4')
    video = cv2.VideoWriter(output_path, fourcc, session['fps'], (width, height))

    # Iterate over each frame and write it to the video
    for f in frames:
        frame_path = os.path.join(frame_folder, f)
        frame = cv2.imread(frame_path)
        video.write(frame)
    video.release()
    cv2.destroyAllWindows()

    return send_file(output_path, as_attachment=True)


@app.route('/upload_canvas', methods=['POST'])
def s2m():
    data = request.get_json()
    drawing_points = [tuple(p) for p in data['points']]
    # Scale drawing_points to image size
    h1 = data['height']
    w1 = data['width']
    h2, w2 = manager_list[session['session_id']].get_size()
    # TODO: potential error with session id
    drawing_points = scale_points(drawing_points, h1, w1, h2, w2)
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

    if mask_list is None or len(mask_list) <= 0:
        # flash('No mask available to propagate')
        return 'Failed to get mask', 400

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
    try:
        inpaint(os.path.join(session['root_folder'], 'frames'),
                os.path.join(session['root_folder'], 'masks'),
                os.path.join(session['root_folder'], 'frames'),
                session.get('fps'))
    except:
        return 'Failed to inpaint', 400

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
