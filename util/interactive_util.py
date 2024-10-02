import os
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from moviepy.video.io.VideoFileClip import VideoFileClip


def convert_to_mp4(file_path):
    """
    Converts a saved video file to mp4 and deletes the original file

    :param file_path: The path to the video
    :return: The filename with a mp4 ending
    """

    video_name, extension = os.path.splitext(file_path)
    # Return if file is already an mp4
    if extension == '.mp4':
        return file_path

    video = VideoFileClip(file_path)
    output_filepath = video_name + '.mp4'
    video.write_videofile(output_filepath)

    video.close()
    os.remove(file_path)  # Delete original file
    return output_filepath


def reduce_fps(file_path, target_fps=30):
    video = VideoFileClip(file_path)
    video_name, extension = os.path.splitext(file_path)
    if video.fps > target_fps:
        output_path = video_name + '_' + str(target_fps) + extension
        video.set_fps(target_fps).write_videofile(output_path, fps=target_fps, codec='libx264')

        video.close()
        os.remove(file_path)  # Delete original file
        return output_path
    else:
        return file_path


def resize_and_save_frames(video_path, output_folder, new_height=360):
    """
    Saves every frame of an uploaded video and reduces its resolution

    :param new_height: New resolution of the video
    :param video_path: Path from root to the video
    :param output_folder: Path from root to the folder that should contain the frames
    """
    os.makedirs(output_folder, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            original_height, original_width = frame.shape[:2]

            # Resize frame
            if original_height > new_height:
                aspect_ratio = original_width / original_height
                new_width = int(aspect_ratio * new_height)
                resized_frame = cv2.resize(frame, (new_width, new_height))
            else:
                resized_frame = frame

            frame_path = os.path.join(output_folder, '{:05}.png'.format(frame_count))
            cv2.imwrite(frame_path, resized_frame)
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
    color_map = [
        [0, 0, 0],
        [255, 0, 0],
        [0, 255, 0],
        [0, 0, 255],
        [255, 0, 255],
        [0, 255, 255],
        [255, 255, 0],
    ]
    color_map_np = np.array(color_map)
    colored_image = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)

    for i in range(len(color_map)):
        colored_image[mask == i, :3] = color_map_np[i]

    colored_image[mask >= 1, 3] = 128

    return colored_image
