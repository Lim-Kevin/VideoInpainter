import os
from os import path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

from lib.Mask_Propagation.dataset.range_transform import im_normalization
from lib.Mask_Propagation.dataset.util import all_to_onehot


class MyDataset(Dataset):
    def __init__(self, mask_dir, image_dir, reverse):
        self.image_dir = image_dir
        self.mask_dir = mask_dir

        # Pre-reading
        self.frames = sorted(os.listdir(self.image_dir))
        if reverse:
            self.frames.reverse()

        mask_path = os.path.join(self.mask_dir, os.listdir(self.mask_dir)[0])
        _mask = np.array(Image.open(mask_path).convert("P"))
        self.shape = np.shape(_mask)

        self.im_transform = transforms.Compose([
            transforms.ToTensor(),
            im_normalization,
            transforms.Resize(480, interpolation=Image.BICUBIC),
        ])

        self.mask_transform = transforms.Compose([
            transforms.Resize(480, interpolation=Image.NEAREST),
        ])

    def __getitem__(self, idx):
        info = {}
        info['num_objects'] = 0
        info['frames'] = self.frames
        info['size'] = self.shape  # Real sizes
        info['gt_obj'] = {}  # Frames with labelled objects

        vid_im_path = self.image_dir
        vid_gt_path = self.mask_dir

        frames = self.frames

        images = []
        masks = []
        for i, f in enumerate(frames):
            img = Image.open(path.join(vid_im_path, f)).convert('RGB')
            images.append(self.im_transform(img))

            mask_file = path.join(vid_gt_path, f)
            if path.exists(mask_file):
                masks.append(np.array(Image.open(mask_file).convert('P'), dtype=np.uint8))
                this_labels = np.unique(masks[-1])
                this_labels = this_labels[this_labels != 0]
                info['gt_obj'][i] = this_labels
            else:
                # Mask not exists -> nothing in it
                masks.append(np.zeros(self.shape))

        images = torch.stack(images, 0)
        masks = np.stack(masks, 0)

        # Construct the forward and backward mapping table for labels
        labels = np.unique(masks).astype(np.uint8)
        labels = labels[labels != 0]
        info['label_convert'] = {}
        info['label_backward'] = {}
        idx = 1
        for l in labels:
            info['label_convert'][l] = idx
            info['label_backward'][idx] = l
            idx += 1
        masks = torch.from_numpy(all_to_onehot(masks, labels)).float()

        # Resize to 480p
        masks = self.mask_transform(masks)
        masks = masks.unsqueeze(2)

        info['labels'] = labels

        data = {
            'rgb': images,
            'gt': masks,
            'info': info,
        }

        return data

    def __len__(self):
        return 1