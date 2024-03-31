import os

import cv2
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


def get_num_frames(video_path):
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print("Error: Unable to open video.")
        return None
    num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    video.release()
    return num_frames
