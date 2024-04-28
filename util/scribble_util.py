from io import BytesIO

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
