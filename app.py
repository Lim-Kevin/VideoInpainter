import os
import shutil
import uuid

from flask import Flask, flash, request, redirect, send_from_directory, render_template, send_file, url_for, \
    session
from werkzeug.utils import secure_filename

from util.MiVOS_util import MiVOS_Manager
from util.interactive_util import array_to_bytesio, get_video_info, save_frames

UPLOAD_FOLDER = 'app/uploads'  # Folder where images should be saved to
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'gif', 'mpeg', 'mov', 'webm', 'flv'}

app = Flask(__name__, template_folder='app/template', static_folder='app/static')

SECRET_KEY = os.urandom(12)  # Set the secret key to a string of random symbols
app.secret_key = SECRET_KEY

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.add_url_rule('/app/uploads/<name>', endpoint='download_file', build_only=True)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size of 16 MB
mivos_manager = MiVOS_Manager()


# TODO: Use flashes
# TODO: Add progressbars in UI
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
            session['video_uploaded'] = True
            session['video_name'] = secure_filename(file.filename)

            folder_name = str(uuid.uuid4())
            session['root_folder'] = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
            os.makedirs(session['root_folder'])
            # Save video
            file_path = os.path.join(session['root_folder'], session['video_name'])
            file.save(file_path)

            # Save frames
            frame_folder = os.path.join(session['root_folder'], 'frames')
            save_frames(file_path, frame_folder)
            session['num_frames'], session['fps'] = get_video_info(file_path)
            session['frame_links'] = [os.path.join(frame_folder, '{:05}.png'.format(i)) for i in
                                      range(session['num_frames'])]

            mivos_manager.setup(file_path)
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
    # image = mivos_manager.show_current_frame(int(num))
    # image_io = array_to_bytesio(image)
    # return send_file(image_io, mimetype='image/png')
    return send_from_directory(os.path.join(session['root_folder'], 'frames'), '{:05}.png'.format(int(num)))


@app.route('/upload_canvas', methods=['POST'])
def s2m():
    data = request.get_json()
    drawing_points = [tuple(p) for p in data]
    mask = mivos_manager.on_drawn(drawing_points)
    mask_io = array_to_bytesio(mask)

    return send_file(mask_io, mimetype='image/png')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
