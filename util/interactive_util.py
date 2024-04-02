import os

import cv2
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
            frame_path = os.path.join(output_folder, 'frame%d.png' % frame_count)
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


def resize_image_to_frame(image, frame_path):
    """
    Takes in an image and makes it the same size as the video
    :param image: Image to be resized
    :param frame_path: Path to the frame image
    """
    frame = Image.open(frame_path)
    width, height = frame.size
    resized_image = image.resize((width, height))
    return resized_image
