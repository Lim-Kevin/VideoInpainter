import cv2

from lib.MiVOS_STCN.interact.interaction import ScribbleInteraction


class MyScribbleInteraction(ScribbleInteraction):
    def __init__(self, image, prev_mask, true_size, controller, num_objects):
        super().__init__(image, prev_mask, true_size, controller, num_objects)

    def push_drawing(self, drawing_points, k=1):
        """
        Uploads a drawing for the scribble to mask interaction
        :param drawing_points: Points used in the drawing, without connection lines
        :param k: Object id, 0 for negative scribbles, 1 else
        """
        self.curr_path[k] = drawing_points
        selected = self.curr_path[k]

        for i in range(len(selected) - 1):
            cv2.line(self.drawn_map, selected[i], selected[i + 1], k, thickness=self.size)
