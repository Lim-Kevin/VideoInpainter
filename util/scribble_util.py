from io import BytesIO

import cv2
import numpy as np
from PIL import Image

from lib.MiVOS_STCN.interact.interaction import ScribbleInteraction


class MyScribbleInteraction(ScribbleInteraction):
    def __init__(self, image, prev_mask, true_size, controller, num_objects):
        super().__init__(image, prev_mask, true_size, controller, num_objects)

    def push_drawing(self, drawing_points, k=1):
        """
        Uploads a drawing for the scribble to mask interaction
        :param drawing_points: Points used in the drawing, without connection lines
        :param k: Object id in case there are multiple objects
        """
        self.curr_path[k] = drawing_points
        selected = self.curr_path[k]
        if len(selected) >= 2:
            self.drawn_map = cv2.line(self.drawn_map,
                                      (int(round(selected[-2][0])), int(round(selected[-2][1]))),
                                      (int(round(selected[-1][0])), int(round(selected[-1][1]))),
                                      k, thickness=self.size)


def comp_mask(mask):
    """
    Makes an image where the mask is colored and slightly transparent
    :param mask: a 1-channel image with 1 where the mask is
    :return: a 4-channel image
    """
    output = np.zeros((*mask.shape, 4), dtype=np.uint8)
    output[mask == 1, :3] = [255, 0, 0]
    output[mask == 1, 3] = 128
    return output

    return output
