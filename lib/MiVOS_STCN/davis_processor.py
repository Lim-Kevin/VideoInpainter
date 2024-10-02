import cv2
import numpy as np
import torch

from lib.MiVOS_STCN.davisinteractive.utils.scribbles import scribbles2mask
from lib.MiVOS_STCN.inference_core import InferenceCore
from lib.MiVOS_STCN.model.aggregate import aggregate_wbg
from lib.MiVOS_STCN.util.tensor_util import pad_divide_by


class DAVISProcessor:
    """
    Acts as the junction between DAVIS interactive track and our inference_core
    """

    def __init__(self, prop_net, fuse_net, s2m_net, images, num_objects, device='cuda:0'):
        self.s2m_net = s2m_net.to(device, non_blocking=True)

        images, self.pad = pad_divide_by(images, 16, images.shape[-2:])
        self.device = device

        # Padded dimensions
        nh, nw = images.shape[-2:]
        self.nh, self.nw = nh, nw

        # True dimensions
        t = images.shape[1]
        h, w = images.shape[-2:]

        self.k = num_objects
        self.t, self.h, self.w = t, h, w

        self.interacted_count = 0
        self.davis_schedule = [2, 5, 7]

        self.processor = InferenceCore(prop_net, fuse_net, images, num_objects, mem_profile=0, device=device)

    def to_mask(self, scribble, single_object=False):
        # First we select the only frame with scribble
        all_scr = scribble['scribbles']
        # all_scr is a list. len(all_scr) == total number of frames
        for idx, s in enumerate(all_scr):
            # The only non-empty element in all_scr is the frame that has been interacted with
            if len(s) != 0:
                scribble['scribbles'] = [s]
                # since we break here, idx will remain at the interacted frame and can be used below
                break

        # Pass to DAVIS to change the path to an array
        scr_mask = scribbles2mask(scribble, (self.h, self.w), single_object=single_object)[0]

        # Run our S2M
        kernel = np.ones((3, 3), np.uint8)
        mask = torch.zeros((self.k, 1, self.nh, self.nw), dtype=torch.float32, device=self.device)
        for ki in range(1, self.k + 1):
            p_srb = (scr_mask == ki).astype(np.uint8)
            p_srb = cv2.dilate(p_srb, kernel).astype(np.bool)

            n_srb = ((scr_mask != ki) * (scr_mask != -1)).astype(np.uint8)
            n_srb = cv2.dilate(n_srb, kernel).astype(np.bool)

            Rs = torch.from_numpy(np.stack([p_srb, n_srb], 0)).unsqueeze(0).float().to(self.device)
            Rs, _ = pad_divide_by(Rs, 16, Rs.shape[-2:])

            # Use hard mask because we train S2M with such
            inputs = torch.cat([self.processor.get_image_buffered(idx),
                                (self.processor.masks[idx] == ki).to(self.device).float().unsqueeze(0), Rs], 1)
            mask[ki - 1] = torch.sigmoid(self.s2m_net(inputs))
        mask = aggregate_wbg(mask, keep_bg=True, hard=True)
        return mask, idx

    def interact(self, scribble, single_object=False):
        mask, idx = self.to_mask(scribble, single_object=single_object)

        if self.interacted_count == self.davis_schedule[0]:
            # Finish the instant interaction loop for this frame
            self.davis_schedule = self.davis_schedule[1:]
            next_interact = None
            out_masks = self.processor.interact(mask, idx)
        else:
            next_interact = [idx]
            out_masks = self.processor.update_mask_only(mask, idx)

        self.interacted_count += 1

        # Trim paddings
        if self.pad[2] + self.pad[3] > 0:
            out_masks = out_masks[:, self.pad[2]:-self.pad[3], :]
        if self.pad[0] + self.pad[1] > 0:
            out_masks = out_masks[:, :, self.pad[0]:-self.pad[1]]

        return out_masks, next_interact, idx
