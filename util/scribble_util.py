import os
from io import BytesIO

import cv2
import numpy as np
import torch
from PIL import Image

from lib.Scribble_to_Mask.interactive import InteractiveManager
from lib.Scribble_to_Mask.model.network import deeplabv3plus_resnet50 as S2M


class MyManager(InteractiveManager):

    def __init__(self):
        self.color = 255

    def setup_manager(self, image_path, mask_path):
        """
        Copied from Scribble_to_mask submodule
        :param image_path: Path to the saved image the scribble is on
        :param mask_path: Optional path to mask if one already exists
        """

        # network stuff
        net = S2M()
        net.load_state_dict(torch.load('saves/s2m.pth'))
        net = net.cuda().eval()
        torch.set_grad_enabled(False)
        # Reading stuff
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        h, w = image.shape[:2]

        # If a mask already exist, paint on top of it
        if os.path.exists(mask_path):
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        else:
            mask = np.zeros((h, w), dtype=np.uint8)
        super().__init__(net, image, mask)

    # TODO: Add negative scribbles
    def run_s2m(self, p_srb, n_srb=None):
        """
        Generates a mask out of scribbles
        :param p_srb: Positive scribbles
        :param n_srb: Negative scribbles
        :return: A mask as an array
        """

        self.p_srb = p_srb
        np_mask = super().run_s2m()

        threshhold = 0.5
        np_mask = np.where(np_mask < 255 * threshhold, 0, self.color)

        # Change colors to make propagation recognize different objects
        self.color = self.color - 1
        if self.color == 0:
            self.color = 255

        return np_mask


def comp_image(mask_path):
    """
    Puts the mask and the scribbles together into one image
    :param mask_path: The path to the mask
    :return: A composed 4-channel image as a BytesIO object
    """

    image = Image.open(mask_path)
    # 1-channel array, 255 where the mask is
    mask_array = np.array(image)

    # Create an empty 4-channel image
    comp = np.zeros((mask_array.shape[0], mask_array.shape[1], 4), dtype=np.uint8)

    # Red wherever the mask is
    comp[:, :, 0] = mask_array

    # Make the image be transparent where there is no color
    alpha = np.where(mask_array == 0, 0, 128)
    comp[:, :, 3] = alpha

    output = BytesIO()
    temp = Image.fromarray(comp)
    temp.save(output, format='PNG')
    output.seek(0)

    return output
