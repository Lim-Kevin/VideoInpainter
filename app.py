import os
import shutil
import traceback
import uuid
from datetime import timedelta, datetime

import cv2
import numpy as np
from PIL import Image
from flask import Flask, request, redirect, send_from_directory, render_template, send_file, url_for, \
    session
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

from lib.ProPainter.inference_propainter import inpaint
from util.MiVOS_util import MiVOS_Manager
from util.interactive_util import get_video_info, resize_and_save_frames, array_to_bytesio, compose_mask, \
    convert_to_mp4, reduce_fps
from util.scribble_util import scale_points

UPLOAD_FOLDER = 'app/uploads'  # Folder where images should be saved to
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'gif', 'mpeg', 'mov', 'webm', 'flv'}
MAX_CONTENT_LENGTH_IN_MB = 3

app = Flask(__name__, template_folder='app/template', static_folder='app/static')

SECRET_KEY = os.urandom(12)  # Set the secret key to a string of random symbols
app.secret_key = SECRET_KEY

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if os.path.exists(UPLOAD_FOLDER):
    shutil.rmtree(UPLOAD_FOLDER)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH_IN_MB * 1024 * 1024  # Max file size
manager_list = {}

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///videos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Create database
class Video(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # UUID
    root_folder = db.Column(db.String(200), nullable=False)
    fps = db.Column(db.Float, nullable=False)
    num_frames = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# Create the database tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Initialize scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


def delete_old_videos():
    with app.app_context():
        # Delete the video if no interaction happened for 10 minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=10)
        old_videos = Video.query.filter(Video.timestamp < cutoff_time).all()

        for video in old_videos:
            if os.path.exists(video.root_folder):
                shutil.rmtree(video.root_folder)
                print('Deleted folder: ' + video.id)
            if video.id in manager_list:
                del manager_list[video.id]
            db.session.delete(video)
            db.session.commit()
            print('Deleted video with ID: ', video.id)


# Schedule the task to run every 10 minutes
scheduler.add_job(id='delete_old_videos', func=delete_old_videos, trigger='interval', minutes=10)


def renew_timestamp(video_id):
    video = Video.query.get(video_id)
    if video:
        video.timestamp = datetime.utcnow()
        db.session.commit()


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    message = session.get('message')
    session['message'] = None
    return render_template('index.html', message=message)


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
            video_name = secure_filename(file.filename)
            video_id = str(uuid.uuid4())

            root_folder = os.path.join(app.config['UPLOAD_FOLDER'], video_id)
            os.makedirs(root_folder)

            # Save video
            file_path = os.path.join(root_folder, video_name)
            file.save(file_path)

            file_path = convert_to_mp4(file_path)
            file_path = reduce_fps(file_path)

            # Save frames
            frame_folder = os.path.join(root_folder, 'frames')
            resize_and_save_frames(file_path, frame_folder)
            num_frames, fps = get_video_info(file_path)

            video = Video(id=video_id, root_folder=root_folder, fps=fps, num_frames=num_frames,
                          timestamp=datetime.utcnow())
            db.session.add(video)
            db.session.commit()

            # Create mask folder and create an empty mask image
            mask_folder = os.path.join(root_folder, 'masks')
            os.makedirs(mask_folder, exist_ok=True)
            temp_img = Image.open(os.path.join(frame_folder, '00000.png'))
            empty_img = Image.new("RGBA", temp_img.size, (0, 0, 0, 0))
            empty_img.save(os.path.join(root_folder, 'empty.png'))

            manager_list[video_id] = MiVOS_Manager(frame_folder)

            return redirect(url_for('mask_page', video_id=video_id))
        else:
            session['message'] = 'Failed to upload file'
            return redirect(url_for('index'))
    return redirect(url_for('index'))


@app.route('/interactive/<video_id>')
def mask_page(video_id):
    video = Video.query.get(video_id)
    if not video:
        session['message'] = 'Session expired'
        return redirect(url_for('index'))
    return render_template('mask.html', num_frames=video.num_frames, fps=video.fps, video_id=video_id)


@app.route('/result/<video_id>')
def result_page(video_id):
    video = Video.query.get(video_id)
    if not video:
        session['message'] = 'Session expired'
        return redirect(url_for('index'))
    return render_template('result.html', num_frames=video.num_frames, fps=video.fps, video_id=video_id)


@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.errorhandler(413)
def request_entity_too_large(error):
    session['message'] = 'File is too large, please submit a file smaller than ' + str(
        MAX_CONTENT_LENGTH_IN_MB) + ' MB'
    return redirect(url_for('index'))


@app.route('/frame/<video_id>/<num>')
def get_frame(video_id, num):
    video = Video.query.get(video_id)
    if not video:
        session['message'] = 'Session expired'
        return redirect(url_for('index'))
    return send_from_directory(os.path.join(video.root_folder, 'frames'), '{:05}.png'.format(int(num)))


@app.route('/mask/<video_id>/<num>')
def get_mask(video_id, num):
    video = Video.query.get(video_id)
    if not video:
        session['message'] = 'Session expired'
        return 'Session expired', 410

    mask_path = os.path.join(video.root_folder, 'masks', '{:05}.png'.format(int(num)))
    if os.path.exists(mask_path):
        image_path = mask_path
    else:
        image_path = os.path.join(video.root_folder, 'empty.png')
    if not os.path.exists(image_path):
        return 'Masks deleted', 404
    return send_file(image_path)


@app.route('/reset_interaction', methods=['POST'])
def reset_interaction():
    data = request.get_json()
    if not data['video_id'] in manager_list:
        session['message'] = 'Session expired'
        return 'Session expired', 410
    renew_timestamp(data['video_id'])
    manager_list[data['video_id']].reset_this_interaction()
    return 'Reset interaction', 200


@app.route('/reset', methods=['POST'])
def reset():
    data = request.get_json()
    video = Video.query.get(data['video_id'])
    if not video:
        session['message'] = 'Session expired'
        return 'Session expired', 410
    video_id = video.id
    root_folder = video.root_folder

    renew_timestamp(video_id)
    manager_list[video_id].on_reset()

    # Delete mask file
    mask_path = os.path.join(root_folder, 'masks', '{:05}.png'.format(int(data['frame_num'])))
    if os.path.exists(mask_path):
        os.remove(mask_path)

    empty_image = os.path.join(root_folder, 'empty.png')
    return send_file(empty_image)


@app.route('/undo', methods=['POST'])
def undo():
    data = request.get_json()
    video = Video.query.get(data['video_id'])
    if not video:
        session['message'] = 'Session expired'
        return 'Session expired', 410
    video_id = video.id
    root_folder = video.root_folder

    renew_timestamp(video_id)
    mask = manager_list[video_id].on_undo()

    mask_folder = os.path.join(root_folder, 'masks')
    mask = compose_mask(mask)

    img = Image.fromarray(mask)
    img.save(os.path.join(mask_folder, '{:05d}.png'.format(data['frame_num'])))

    # Send current mask for instant feedback
    mask_io = array_to_bytesio(mask)

    response = send_file(mask_io, mimetype='image/jpeg')
    if np.all(mask == 0):
        response.headers['error'] = 'Mask is empty'
    return response


@app.route('/save_video', methods=['POST'])
def save_video():
    data = request.get_json()
    video = Video.query.get(data['video_id'])
    if not video:
        session['message'] = 'Session expired'
        return 'Session expired', 410
    root_folder = video.root_folder
    fps = video.fps

    frame_folder = os.path.join(root_folder, 'frames')
    frames = [f for f in os.listdir(frame_folder)]
    frames.sort()

    first_frame_path = os.path.join(frame_folder, frames[0])
    frame = cv2.imread(first_frame_path)
    height, width, layers = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_path = os.path.join(root_folder, 'inpainted.mp4')
    video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

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
    video = Video.query.get(data['video_id'])
    if not video:
        session['message'] = 'Session expired'
        return 'Session expired', 410
    video_id = video.id
    root_folder = video.root_folder

    renew_timestamp(video_id)

    drawing_points = [tuple(p) for p in data['points']]
    # Scale drawing_points to image size
    h1 = data['height']
    w1 = data['width']
    h2, w2 = manager_list[video_id].get_size()
    drawing_points = scale_points(drawing_points, h1, w1, h2, w2)
    mask = manager_list[video_id].on_drawn(drawing_points, data['frame_num'], int(data['k']))

    mask_folder = os.path.join(root_folder, 'masks')
    mask = compose_mask(mask)

    img = Image.fromarray(mask)
    img.save(os.path.join(mask_folder, '{:05d}.png'.format(data['frame_num'])))

    # Return current mask for instant feedback
    mask_io = array_to_bytesio(mask)
    return send_file(mask_io, mimetype='image/png')


@app.route('/propagate', methods=['POST'])
def propagate():
    data = request.get_json()
    video = Video.query.get(data['video_id'])
    if not video:
        session['message'] = 'Session expired'
        return 'Session expired', 410
    video_id = video.id
    root_folder = video.root_folder

    renew_timestamp(video_id)
    mask_list = manager_list[video_id].on_run()

    mask_folder = os.path.join(root_folder, 'masks')
    os.makedirs(mask_folder, exist_ok=True)

    if mask_list is None or len(mask_list) <= 0:
        # flash('No mask available to propagate')
        return 'Failed to get mask', 400

    for i in range(len(mask_list)):
        img = compose_mask(mask_list[i])
        img = Image.fromarray(img)
        img.save(os.path.join(mask_folder, '{:05d}.png'.format(i)))

    return 'Propagated', 200


@app.route('/inpaint', methods=['POST'])
def inpaint_video():
    data = request.get_json()
    video = Video.query.get(data['video_id'])
    if not video:
        session['message'] = 'Session expired'
        return 'Session expired', 410
    video_id = video.id
    root_folder = video.root_folder

    renew_timestamp(video_id)

    try:
        inpaint(os.path.join(root_folder, 'frames'),
                os.path.join(root_folder, 'masks'),
                os.path.join(root_folder, 'frames'))
    except TypeError:
        return 'No mask', 404
    except Exception as e:
        print('Inpainting error: ', e)
        traceback.print_exc()
        return 'Inpainting error', 400

    return redirect(url_for('result_page', video_id=video_id))


@app.route('/again', methods=['POST'])
def inpaint_again():
    data = request.get_json()
    video = Video.query.get(data['video_id'])
    if not video:
        session['message'] = 'Session expired'
        return 'Session expired', 410
    video_id = video.id
    root_folder = video.root_folder

    renew_timestamp(video_id)
    mask_folder = os.path.join(root_folder, 'masks')
    frame_folder = os.path.join(root_folder, 'frames')
    # Delete masks
    if os.path.exists(mask_folder):
        shutil.rmtree(mask_folder)
        os.makedirs(mask_folder, exist_ok=True)
    # initialise frame
    manager_list[video_id] = MiVOS_Manager(frame_folder)
    return redirect(url_for('mask_page', video_id=video_id))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
