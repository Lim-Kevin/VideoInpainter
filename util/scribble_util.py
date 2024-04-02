import cv2
import numpy as np
import torch
from submodules.Scribble_to_Mask.model.network import deeplabv3plus_resnet50 as S2M

from submodules.Scribble_to_Mask.interactive import InteractiveManager


def setup_manager(image, mask=None):
    """
    Copied from Scribble_to_mask submodule
    :param image: Path to the saved image the scribble is on
    :param mask: Optional path to mask if one already exists
    """
    # network stuff
    net = S2M()
    net.load_state_dict(torch.load('submodules/Scribble_to_Mask/saves/s2m.pth'))
    net = net.cuda().eval()
    torch.set_grad_enabled(False)
    # Reading stuff
    image = cv2.imread(image, cv2.IMREAD_COLOR)
    h, w = image.shape[:2]
    if mask is None:
        mask = np.zeros((h, w), dtype=np.uint8)
    else:
        mask = cv2.imread(mask, cv2.IMREAD_GRAYSCALE)

    return InteractiveManager(net, image, mask)
