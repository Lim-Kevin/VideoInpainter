import cv2
import numpy as np
import torch
from lib.Scribble_to_Mask.model.network import deeplabv3plus_resnet50 as S2M
from lib.Scribble_to_Mask.interactive import InteractiveManager


class MyManager(InteractiveManager):
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
        np_mask = np.where(np_mask < 255 * threshhold, 0, 255)
        return np_mask


def setup_manager(image_path, mask=None):
    """
    Copied from Scribble_to_mask submodule
    :param image_path: Path to the saved image the scribble is on
    :param mask: Optional path to mask if one already exists
    """
    # network stuff
    net = S2M()
    net.load_state_dict(torch.load('saves/s2m.pth'))
    net = net.cuda().eval()
    torch.set_grad_enabled(False)
    # Reading stuff
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    h, w = image.shape[:2]
    if mask is None:
        mask = np.zeros((h, w), dtype=np.uint8)
    else:
        mask = cv2.imread(mask, cv2.IMREAD_GRAYSCALE)

    return MyManager(net, image, mask)


def comp_image(mask_array, p_srb=None, n_srb=None):
    """
    Puts the mask and the scribbles together into one image
    :param mask_array:The mask as a 1-channel array, 255 where the mask is
    :param p_srb: The positive scribble, 1 where the scribble is
    :param n_srb: The negative scribble, 1 where the scribble is
    :return: A composed 4-channel image as an array
    """
    # Create an empty 4-channel image
    comp = np.zeros((mask_array.shape[0], mask_array.shape[1], 4), dtype=np.uint8)

    # TODO: add scribbles to the image
    # Red wherever the mask is
    comp[:, :, 0] = mask_array

    # Make the image be transparent where there is no color
    alpha = np.where(mask_array == 0, 0, 128)
    comp[:, :, 3] = alpha
    return comp
