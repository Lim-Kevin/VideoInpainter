import cv2

from lib.MiVOS_STCN.interact.interaction import ScribbleInteraction


class MyScribbleInteraction(ScribbleInteraction):
    def __init__(self, image, prev_mask, true_size, controller, num_objects):
        super().__init__(image, prev_mask, true_size, controller, num_objects)

    def push_drawing(self, drawing_points, k=1):
        """
        Saves a drawing for the scribble to mask interaction
        :param drawing_points: Points used in the drawing, without connection lines
        :param k: Object id, 0 for negative scribbles, 1 else
        """

        self.curr_path[k] = drawing_points
        selected = self.curr_path[k]

        for i in range(len(selected) - 1):
            cv2.line(self.drawn_map, selected[i], selected[i + 1], k, thickness=self.size)


def scale_points(points, h1, w1, h2, w2):
    """
    Scaling points in a list from (h1, w1) to (h2, w2)
    :param points:
    :param h1: Scaling from this height
    :param w1: Scaling from this width
    :param h2: Scaling to this height
    :param w2: Scaling to this width
    :return: List of scaled points
    """
    h_scale = h2 / h1
    w_scale = w2 / w1
    res = []
    for x, y in points:
        scaled_x = int(x * w_scale)
        scaled_y = int(y * h_scale)
        res.append((scaled_x, scaled_y))
    return res
