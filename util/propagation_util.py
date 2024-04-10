import os
from os import path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from progressbar import progressbar
from torch.utils.data import DataLoader

from lib.Mask_Propagation.inference_core_yv import InferenceCore
from lib.Mask_Propagation.model.eval_network import PropagationNetwork
from util.MyDataset import MyDataset


# TODO: Add functionality of propagating masks multiple times
def propagate_all(frames_path, masks_path, out_path):
    """
    Propagate every frame for a given mask
    :param frames_path: Path to folder with frames
    :param masks_path: Path to folder with masks
    """

    frames_list = sorted(os.listdir(frames_path))
    masks_list = sorted(os.listdir(masks_path))

    # Can't propagate backwards, if the mask is on the first frame,
    if frames_list[0] != masks_list[0]:
        dataset_reverse = MyDataset(mask_dir=masks_path, image_dir=frames_path, reverse=True)
        propagate(dataset_reverse, out_path)
    # Can't propagate forward, if the masks is on the first frame,
    elif frames_list[-1] != masks_list[0]:
        dataset = MyDataset(mask_dir=masks_path, image_dir=frames_path, reverse=False)
        propagate(dataset, out_path)


def propagate(dataset, out_path):
    """
    Propagate every frame after a given mask
    :param dataset:
    :param out_path:
    :return:
    """
    model = 'saves/propagation_model.pth'

    # Simple setup
    os.makedirs(out_path, exist_ok=True)
    torch.autograd.set_grad_enabled(False)

    # Setup Dataset
    test_loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=2)

    # Load our checkpoint
    prop_saved = torch.load(model)
    top_k = None
    prop_model = PropagationNetwork(top_k=top_k, km=5.6).cuda().eval()
    prop_model.load_state_dict(prop_saved)

    # Start eval
    for data in progressbar(test_loader, max_value=len(test_loader), redirect_stdout=True):
        rgb = data['rgb']
        msk = data['gt'][0]
        info = data['info']
        k = len(info['labels'][0])
        gt_obj = info['gt_obj']
        size = info['size']

        torch.cuda.synchronize()

        # Frames with labels, but they are not exhaustively labeled
        frames_with_gt = sorted(list(gt_obj.keys()))

        processor = InferenceCore(prop_model, rgb, num_objects=k)
        # min_idx tells us the starting point of propagation
        # Propagating before there are labels is not useful
        min_idx = 99999
        for i, frame_idx in enumerate(frames_with_gt):
            min_idx = min(frame_idx, min_idx)
            # Note that there might be more than one label per frame
            obj_idx = gt_obj[frame_idx][0].tolist()
            # Map the possibly non-continuous labels into a continuous scheme
            obj_idx = [info['label_convert'][o].item() for o in obj_idx]

            # Append the background label
            with_bg_msk = torch.cat([
                1 - torch.sum(msk[:, frame_idx], dim=0, keepdim=True),
                msk[:, frame_idx],
            ], 0).cuda()

            # We perform propagation from the current frame to the next frame with label
            if i == len(frames_with_gt) - 1:
                processor.interact(with_bg_msk, frame_idx, rgb.shape[1], obj_idx)
            else:
                processor.interact(with_bg_msk, frame_idx, frames_with_gt[i + 1] + 1, obj_idx)

        # Do unpad -> upsample to original size (we made it 480p)
        out_masks = torch.zeros((processor.t, 1, *size), dtype=torch.uint8, device='cuda')
        for ti in range(processor.t):
            prob = processor.prob[:, ti]

            if processor.pad[2] + processor.pad[3] > 0:
                prob = prob[:, :, processor.pad[2]:-processor.pad[3], :]
            if processor.pad[0] + processor.pad[1] > 0:
                prob = prob[:, :, :, processor.pad[0]:-processor.pad[1]]

            prob = F.interpolate(prob, size, mode='bilinear', align_corners=False)
            out_masks[ti] = torch.argmax(prob, dim=0)

        out_masks = (out_masks.detach().cpu().numpy()[:, 0]).astype(np.uint8)

        # Remap the indices to the original domain
        idx_masks = np.zeros_like(out_masks)
        for i in range(1, k + 1):
            backward_idx = info['label_backward'][i].item()
            idx_masks[out_masks == i] = backward_idx

        torch.cuda.synchronize()

        # Save the results
        this_out_path = path.join(out_path)
        os.makedirs(this_out_path, exist_ok=True)
        for f in range(idx_masks.shape[0]):
            if f >= min_idx:
                img_E = Image.fromarray(idx_masks[f])
                img_E.save(os.path.join(this_out_path, info['frames'][f][0]))

        del rgb
        del msk
        del processor
