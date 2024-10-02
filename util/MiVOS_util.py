from collections import deque

import numpy as np
import torch

from lib.MiVOS_STCN.inference_core import InferenceCore
from lib.MiVOS_STCN.interact.interactive_utils import images_to_torch, load_images
from lib.MiVOS_STCN.interact.s2m_controller import S2MController
from lib.MiVOS_STCN.model.fusion_net import FusionNet
from lib.MiVOS_STCN.model.propagation.prop_net import PropagationNetwork
from lib.MiVOS_STCN.model.s2m.s2m_network import deeplabv3plus_resnet50 as S2M
from util.scribble_util import MyScribbleInteraction


class MiVOS_Manager:
    def __init__(self, image_folder, num_objects=1):
        # Check if CUDA is available
        device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # Set up models
        prop_saved = torch.load('saves/stcn.pth', map_location=device)
        prop_model = PropagationNetwork().to(device).eval()
        prop_model.load_state_dict(prop_saved)

        fusion_saved = torch.load('saves/fusion_stcn.pth', map_location=device)
        fuse_model = FusionNet().to(device).eval()
        fuse_model.load_state_dict(fusion_saved)

        s2m_saved = torch.load('saves/s2m.pth', map_location=device)
        s2m_model = S2M().to(device).eval()
        s2m_model.load_state_dict(s2m_saved)

        # Loads the images/masks
        # Set resolution=-1 to use original size
        self.images = load_images(image_folder)
        self.num_frames, self.height, self.width = self.images.shape[:3]
        self.num_objects = num_objects

        self.s2m_controller = S2MController(s2m_model, num_objects=self.num_objects, ignore_class=255, device=device)

        self.processor = InferenceCore(prop_model, fuse_model, images_to_torch(self.images, device=device),
                                       self.num_objects, mem_freq=5, mem_profile=0, device=device)

        # initialize visualization
        self.current_mask = np.zeros((self.num_frames, self.height, self.width), dtype=np.uint8)
        self.vis_map = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.vis_alpha = np.zeros((self.height, self.width, 1), dtype=np.float32)
        self.brush_vis_map = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.brush_vis_alpha = np.zeros((self.height, self.width, 1), dtype=np.float32)
        self.vis_hist = deque(maxlen=100)

        # self.cursur is set to the number of the current frame we look at
        self.cursur = 0

        # initialize action
        self.interactions = {}
        self.interactions['interact'] = [[] for _ in range(self.num_frames)]
        self.interactions['annotated_frame'] = []
        self.this_frame_interactions = []
        self.interaction = None
        self.reset_this_interaction()
        self.interacted_mask = None

    def clear_visualization(self):
        self.vis_map.fill(0)
        self.vis_alpha.fill(0)
        self.vis_hist.clear()
        self.vis_hist.append((self.vis_map.copy(), self.vis_alpha.copy()))

    def reset_this_interaction(self):
        self.complete_interaction()
        self.clear_visualization()
        self.interaction = None
        self.this_frame_interactions = []

    def on_run(self):
        """
        Propagate the masks
        """

        if self.interacted_mask is None:
            print('Cannot propagate! No interacted mask!')
            return

        # Create a list of propagated masks
        with torch.cuda.amp.autocast(enabled=True) and torch.set_grad_enabled(False):
            self.current_mask = self.processor.interact(self.interacted_mask, self.cursur)

        self.interacted_mask = None
        self.reset_this_interaction()

        print('Propagation finished')
        return self.current_mask

    def on_drawn(self, drawing_points, frame_num, k):
        """
        Execute after a scribble was drawn
        :param drawing_points: The points in the scribble as a list of tuples (only points, no connection lines)
        :param frame_num: The number of the frame that is being drawn on
        :param k: Object id, 0 for negative scribbles, else 1
        :return: Predicted mask of the scribbles
        """
        self.cursur = frame_num

        # Push last vis map into history
        self.vis_hist.append((self.vis_map.copy(), self.vis_alpha.copy()))

        prev_hard_mask = self.processor.masks[self.cursur]
        image = self.processor.images[:, self.cursur]
        h, w = self.height, self.width
        if self.interaction is None:
            self.interaction = MyScribbleInteraction(image, prev_hard_mask, (h, w), self.s2m_controller,
                                                     self.num_objects)

        self.interaction.push_drawing(drawing_points, k)

        interaction = self.interaction
        interaction.end_path()

        with torch.cuda.amp.autocast(enabled=True) and torch.set_grad_enabled(False):
            self.interacted_mask = interaction.predict()

        return self.update_interacted_mask()

    def on_undo(self):
        if self.interaction is None:
            if len(self.this_frame_interactions) > 1:
                self.this_frame_interactions = self.this_frame_interactions[:-1]
                self.interacted_mask = self.this_frame_interactions[-1].predict()
            else:
                self.reset_this_interaction()
                self.interacted_mask = self.processor.prob[:, self.cursur].clone()
        else:
            if self.interaction.can_undo():
                self.interacted_mask = self.interaction.undo()
            else:
                if len(self.this_frame_interactions) > 0:
                    self.interaction = None
                    self.interacted_mask = self.this_frame_interactions[-1].predict()
                else:
                    self.reset_this_interaction()
                    self.interacted_mask = self.processor.prob[:, self.cursur].clone()

        # Update visualization
        if len(self.vis_hist) > 0:
            # Might be empty if we are undoing the entire interaction
            self.vis_map, self.vis_alpha = self.vis_hist.pop()

        # Commit changes
        return self.update_interacted_mask()

    def on_reset(self):
        # DO not edit prob -- we still need the mask diff
        self.processor.masks[self.cursur].zero_()
        self.processor.np_masks[self.cursur].fill(0)
        self.current_mask[self.cursur].fill(0)
        self.reset_this_interaction()
        # return self.current_mask[self.cursur]

    def update_interacted_mask(self):
        """
        Calculate the currently interacted mask
        :return: a transparent image with the mask in red
        """

        self.processor.update_mask_only(self.interacted_mask, self.cursur)
        self.current_mask[self.cursur] = self.processor.np_masks[self.cursur]
        return self.current_mask[self.cursur]

    def complete_interaction(self):
        if self.interaction is not None:
            self.clear_visualization()

            self.interactions['annotated_frame'].append(self.cursur)
            self.interactions['interact'][self.cursur].append(self.interaction)
            self.this_frame_interactions.append(self.interaction)
            self.interaction = None

    def get_size(self):
        return self.height, self.width
