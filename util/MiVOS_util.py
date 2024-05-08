import os
from collections import deque

import numpy as np
import torch
from PIL.Image import Image

from lib.MiVOS_STCN.inference_core import InferenceCore
from lib.MiVOS_STCN.interact.interactive_utils import load_video, images_to_torch
from lib.MiVOS_STCN.interact.s2m_controller import S2MController
from lib.MiVOS_STCN.model.fusion_net import FusionNet
from lib.MiVOS_STCN.model.propagation.prop_net import PropagationNetwork
from lib.MiVOS_STCN.model.s2m.s2m_network import deeplabv3plus_resnet50 as S2M
from util.scribble_util import MyScribbleInteraction


class MiVOS_Manager:
    def __init__(self, video_path, resolution=480):
        # Set up models
        # Load our checkpoint
        prop_saved = torch.load('saves/stcn.pth')
        prop_model = PropagationNetwork().cuda().eval()
        prop_model.load_state_dict(prop_saved)

        fusion_saved = torch.load('saves/fusion_stcn.pth')
        fuse_model = FusionNet().cuda().eval()
        fuse_model.load_state_dict(fusion_saved)

        # Loads the S2M model
        s2m_saved = torch.load('saves/s2m.pth')
        s2m_model = S2M().cuda().eval()
        s2m_model.load_state_dict(s2m_saved)

        # Loads the images/masks
        # Set resolution=-1 to use original size
        self.images = load_video(video_path, resolution)
        self.num_frames, self.height, self.width = self.images.shape[:3]
        self.num_objects = 1

        self.s2m_controller = S2MController(s2m_model, num_objects=self.num_objects, ignore_class=255)

        self.processor = InferenceCore(prop_model, fuse_model, images_to_torch(self.images, device='cpu'),
                                       self.num_objects, mem_freq=5, mem_profile=0)

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
        # self.pressed = False
        # self.right_click = False
        self.interacted_mask = None

    def save(self):
        out_folder = 'out'
        mask_dir = os.path.join(out_folder, 'mask')

        os.makedirs(mask_dir, exist_ok=True)

        for i in range(self.num_frames):
            # Save mask
            mask = Image.fromarray(self.current_mask[i]).convert('P')
            # mask.putpalette(palette)
            mask.save(os.path.join(mask_dir, '{:05d}.png'.format(i)))

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
        # self.undo_button.setDisabled(True)

    def on_run(self, frame_num):

        """
        Propagation
        """
        self.cursur = frame_num

        if self.interacted_mask is None:
            print('Cannot propagate! No interacted mask!')
            return
        # self.interacted_mask = torch.softmax(self.interacted_mask*1000, dim=0)

        # A list of propagated masks

        with torch.cuda.amp.autocast(enabled=True) and torch.set_grad_enabled(False):
            self.current_mask = self.processor.interact(self.interacted_mask, self.cursur)

        self.interacted_mask = None
        # clear scribble and reset
        self.reset_this_interaction()
        # return self.show_mask(self.cursur)

        print('Propagation finished')
        return self.current_mask

        # self.progress.setFormat('Idle')
        # self.progress.setValue(0)

        # TODO: Save mask frames after propagating
        # self.user_timer.start()

    def on_drawn(self, drawing_points, frame_num, k):
        """
        Execute after a scribble was drawn
        :param drawing_points: The points in the scribble as a list of tuples (only points, no connection lines)
        :param frame_num: The number of the frame that is being drawn on
        :param k: Object id, 0 for negative scribbles, else 1
        :return: Predicted mask of the scribbles
        """
        self.cursur = frame_num

        # on_press()
        # self.right_click = (event.button() != 1)

        # Push last vis map into history
        self.vis_hist.append((self.vis_map.copy(), self.vis_alpha.copy()))

        prev_hard_mask = self.processor.masks[self.cursur]
        image = self.processor.images[:, self.cursur]
        h, w = self.height, self.width

        if self.interaction is None:
            self.interaction = MyScribbleInteraction(image, prev_hard_mask, (h, w), self.s2m_controller,
                                                     self.num_objects)

        # on_motion()
        self.interaction.push_drawing(drawing_points, k)

        # on_release()
        print('Interaction at frame %d.' % self.cursur)

        interaction = self.interaction
        interaction.end_path()

        with torch.cuda.amp.autocast(enabled=True) and torch.set_grad_enabled(False):
            self.interacted_mask = interaction.predict()

        return self.update_interacted_mask()

        # self.pressed = self.right_click = False
        # self.undo_button.setDisabled(False)

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
        self.update_interacted_mask()

    def on_reset(self):
        # DO not edit prob -- we still need the mask diff

        self.processor.masks[self.cursur].zero_()
        self.processor.np_masks[self.cursur].fill(0)
        self.current_mask[self.cursur].fill(0)
        self.reset_this_interaction()
        # self.show_mask(self.cursur)

    def on_press(self):
        # self.right_click = (event.button() != 1)

        # Push last vis map into history
        self.vis_hist.append((self.vis_map.copy(), self.vis_alpha.copy()))

        prev_hard_mask = self.processor.masks[self.cursur]
        image = self.processor.images[:, self.cursur]
        h, w = self.height, self.width

        if self.interaction is None:
            self.interaction = MyScribbleInteraction(image, prev_hard_mask, (h, w), self.s2m_controller,
                                                     self.num_objects)

        # Just motion it as the first step
        # Show frame and mask
        # self.on_motion(event)

    def update_interacted_mask(self):
        """
        Calculate the currently interacted mask
        :return: a transparent image with the mask in red
        """

        self.processor.update_mask_only(self.interacted_mask, self.cursur)
        self.current_mask[self.cursur] = self.processor.np_masks[self.cursur]
        return self.current_mask[self.cursur]

    def get_mask(self, num):
        return self.current_mask[num]

    def get_masks(self):
        return self.current_mask

    def complete_interaction(self):
        if self.interaction is not None:
            self.clear_visualization()

            self.interactions['annotated_frame'].append(self.cursur)
            self.interactions['interact'][self.cursur].append(self.interaction)
            self.this_frame_interactions.append(self.interaction)
            self.interaction = None
            # self.undo_button.setDisabled(False)
