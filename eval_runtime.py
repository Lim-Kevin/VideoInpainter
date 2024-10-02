import json
import os
import shutil
import statistics
import time
from argparse import ArgumentParser

import numpy as np
from PIL import Image

from lib.ProPainter.inference_propainter import inpaint
from util.MiVOS_util import MiVOS_Manager
from util.interactive_util import compose_mask

"""
Arguments loading
"""
parser = ArgumentParser()
parser.add_argument('--dataset', default='datasets/runtime_dataset')
parser.add_argument('--bounding_box', action='store_true')
parser.add_argument('--single_object', action='store_true')
parser.add_argument('--output')
args = parser.parse_args()

dataset_path = args.dataset
output_path = args.output
os.makedirs(output_path, exist_ok=True)

resolution_path = os.path.join(dataset_path, 'JPEGImages', '480p')
frames_path = os.path.join(dataset_path, 'JPEGImages', 'Frames1000')
resolutions = [144, 240, 360, 480]
num_frames = [100, 250, 500, 750]

def resize_images(folder_path, new_height, out_path):
    os.makedirs(out_path, exist_ok=True)
    for file in os.listdir(folder_path):
        image_path = os.path.join(folder_path, file)

        img = Image.open(image_path)
        width, height = img.size

        new_width = int((new_height / height) * width)

        resized_img = img.resize((new_width, new_height), Image.BICUBIC)
        resized_img.save(os.path.join(out_path, file))
    return


def change_num_frames(folder_path, num_frames, out_path):
    os.makedirs(out_path, exist_ok=True)
    for i in range(num_frames):
        file = os.listdir(folder_path)[i]
        image_path = os.path.join(folder_path, file)
        img = Image.open(image_path)
        img.save(os.path.join(out_path, file))
    return


def eval_video_runtime(image_folder, out_path, folder):
    mask_start_time = time.time()

    scribble_path = os.path.join(dataset_path, 'Scribbles', video + '.json')
    with open(scribble_path, 'r') as file:
        data = json.load(file)

    if args.single_object:
        num_obj = 1
    else:
        num_obj = data['num_objects']
    manager = MiVOS_Manager(image_folder, num_objects=num_obj)
    height, width = manager.get_size()

    scribbles = data['scribbles']
    for entry in scribbles:
        num_frame = entry['num_frame']
        path = entry['path']
        scaled_path = [(int(x * width), int(y * height)) for x, y in path]
        # s2m
        if args.single_object:
            obj_id = 1
        else:
            obj_id = entry['object_id']
        mask = manager.on_drawn(scaled_path, num_frame, obj_id)

    # Propagation
    mask_list = manager.on_run()

    # Always save masks to simulate actual pipeline
    mask_path = os.path.join(out_path, 'Masks', folder, video)
    os.makedirs(mask_path, exist_ok=True)
    for i in range(len(mask_list)):
        img = compose_mask(mask_list[i])
        img = Image.fromarray(img)
        img.save(os.path.join(mask_path, '{:05d}.png'.format(i)))

    mask_end_time = time.time()
    mask_runtime = mask_end_time - mask_start_time
    inpaint_start_time = time.time()

    # Inpaint and save images
    inpaint(image_folder,
            mask_path,
            os.path.join(out_path, 'Inpaint', folder, video),
            bounding_box=args.bounding_box)

    inpaint_end_time = time.time()
    inpaint_runtime = inpaint_end_time - inpaint_start_time
    inpaint_runtime_per_frame = inpaint_runtime / len(os.listdir(image_folder))
    mask_runtime_per_frame = mask_runtime / len(os.listdir(image_folder))
    return mask_runtime, inpaint_runtime, mask_runtime_per_frame, inpaint_runtime_per_frame


def write_summary(file, details_list, resolution=None, num_frames=None):
    if resolution:
        title = 'Resolution: ' + str(resolution)
    if num_frames:
        title = '#Frames: ' + str(num_frames)
    mask_time_list = [t[1] for t in details_list]
    inpaint_time_list = [t[2] for t in details_list]
    total_time_list = [t[3] for t in details_list]
    mask_runtime_per_frame_list = [t[4] for t in details_list]
    inpaint_runtime_per_frame_list = [t[5] for t in details_list]

    average_mask_time = statistics.mean(mask_time_list)
    average_inpaint_time = statistics.mean(inpaint_time_list)
    average_time = statistics.mean(total_time_list)
    average_mask_per_frame_time = statistics.mean(mask_runtime_per_frame_list)
    average_inpaint_per_frame_time = statistics.mean(inpaint_runtime_per_frame_list)

    print(title, ', Average time: ', round(average_time, 2), ' seconds\n')

    # Write results to text file
    file.write(title + '\n')
    for name, _, _, total, m, i in video_details_list:
        f.write(f'Video: {name.ljust(20)}'
                f'Video segmentation time per frame: {str(round(m, 3)).ljust(6)} seconds, '
                f'Inpainting time per frame: {str(round(i, 3)).ljust(6)} seconds, '
                f'Total time: {str(round(total, 3)).ljust(6)} seconds\n')

    f.write('Average Total Time: ' + str(round(average_time, 3)) + ' seconds\n')
    f.write('Average Video Segmentation Time: ' + str(round(average_mask_time, 3)) + ' seconds\n')
    f.write('Average Inpainting Time: ' + str(round(average_inpaint_time, 3)) + ' seconds\n')
    f.write('Average Video Segmentation Time per frame: ' + str(round(average_mask_per_frame_time, 3)) + ' seconds\n')
    f.write('Average Inpainting Time per frame: ' + str(round(average_inpaint_per_frame_time, 3)) + ' seconds\n')
    f.write('\n')

with open(os.path.join(output_path, 'summary.txt'), 'w') as f:
    # Evaluating with different resolutions
    resolution_folder_list = os.listdir(resolution_path)
    temp_path = os.path.join(output_path, 'temp')
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)
    os.makedirs(temp_path)

    for res in resolutions:
        runtime_list = []
        video_details_list = []
        for video in resolution_folder_list:
            video_path = os.path.join(resolution_path, video)
            print('Evaluating ' + video + ' on resolution: ' + str(res))

            resize_images(video_path, res, temp_path)

            mask_runtime, inpaint_runtime, mask_runtime_per_frame, inpaint_runtime_per_frame = eval_video_runtime(temp_path, output_path, str(res) + 'p')

            # Delete temp folder
            shutil.rmtree(temp_path)
            total_runtime = inpaint_runtime + mask_runtime
            video_details_list.append((video, mask_runtime, inpaint_runtime, total_runtime, mask_runtime_per_frame, inpaint_runtime_per_frame))

            print('Video: ', video, ', Time: ', round(total_runtime, 2), ' seconds\n')
        write_summary(f, video_details_list, resolution=res)

    # Evaluating with different number of frames
    frames_folder_list = os.listdir(frames_path)
    for n in num_frames:
        runtime_list = []
        video_details_list = []
        for video in frames_folder_list:
            video_path = os.path.join(frames_path, video)
            print('Evaluating ' + video + ' on #Frames: ' + str(n))

            change_num_frames(video_path, n, temp_path)
            mask_runtime, inpaint_runtime, mask_runtime_per_frame, inpaint_runtime_per_frame = eval_video_runtime(temp_path, output_path, 'Frames' + str(n))

            # Delete temp folder
            shutil.rmtree(temp_path)
            total_runtime = inpaint_runtime + mask_runtime
            video_details_list.append((video, mask_runtime, inpaint_runtime, total_runtime, mask_runtime_per_frame, inpaint_runtime_per_frame))

            print('Video: ', video, ', Time: ', round(total_runtime, 2), ' seconds\n')
        write_summary(f, video_details_list, num_frames=n)
    f.close()
