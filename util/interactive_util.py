import os
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from moviepy.video.io.VideoFileClip import VideoFileClip


def convert_to_mp4(folder_path, filename):
    """
    Converts a saved video file to mp4

    :param folder_path: Path from root to the folder where the video is saved
    :param filename: Name of the video file
    :return: The filename with a mp4 ending
    """
    file_path = os.path.join(folder_path, filename)

    # Return if file is already an mp4
    if file_path.split('.')[1] == "mp4":
        return filename

    video = VideoFileClip(file_path)
    output_filepath = file_path.split('.')[0] + ".mp4"
    video.write_videofile(output_filepath)

    os.remove(file_path)  # Delete original file
    print(file_path)
    mp4_filename = filename.split('.')[0] + ".mp4"
    return mp4_filename


def save_frames(video_path, output_folder):
    """
    Saves every frame of an uploaded video
    :param video_path: Path from root to the video
    :param output_folder: Path from root to the folder that should contain the frames
    """
    os.makedirs(output_folder, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            frame_path = os.path.join(output_folder, '{:05}.png'.format(frame_count))
            cv2.imwrite(frame_path, frame)
            frame_count += 1
        else:
            break
    cap.release()
    cv2.destroyAllWindows()


def get_video_info(video_path):
    """
    :param video_path: Path from root to the video
    :return: Number of frames and fps of a video
    """
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print("Error: Unable to open video.")
        return None
    num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    video.release()
    return num_frames, fps


def array_to_bytesio(image_array):
    # Convert the NumPy array to an image
    image = Image.fromarray(image_array)

    # Create a BytesIO object to store the image data
    img_io = BytesIO()

    # Save the image to the BytesIO object in PNG format
    image.save(img_io, 'PNG')
    img_io.seek(0)

    return img_io


def compose_mask(mask):
    """
    Makes an image where the mask is colored and slightly transparent
    :param mask: a 1-channel image with 1 where the mask is
    :return: the composed mask as an array
    """
    output = np.zeros((*mask.shape, 4), dtype=np.uint8)
    output[mask == 1, :3] = [255, 0, 0]
    output[mask == 1, 3] = 128
    return output
