import os
import gdown

os.makedirs('saves', exist_ok=True)

# MiVOS models
print('Downloading propagation model...')
gdown.download('https://drive.google.com/uc?id=1mRrE0uCI2ktdWlUgapJI_KmgeIiF2eOm', output='saves/stcn.pth', quiet=False)

print('Downloading fusion model...')
gdown.download('https://drive.google.com/uc?id=1MAbWHrOjlze9vPQdW-HxMnvjPpaZlfLv', output='saves/fusion_stcn.pth', quiet=False)

print('Downloading s2m model...')
gdown.download('https://drive.google.com/uc?id=1HKwklVey3P2jmmdmrACFlkXtcvNxbKMM', output='saves/s2m.pth', quiet=False)

# ProPainter models
print('Downloading RAFT model')
gdown.download('https://github.com/sczhou/ProPainter/releases/download/v0.1.0/raft-things.pth', output='saves/raft_things.pth', quiet=False)

print('Downloading flow competition model')
gdown.download('https://github.com/sczhou/ProPainter/releases/download/v0.1.0/recurrent_flow_completion.pth', output='saves/recurrent_flow_completion.pth', quiet=False)


print('Downloading ProPainter model')
gdown.download('https://github.com/sczhou/ProPainter/releases/download/v0.1.0/ProPainter.pth', output='saves/ProPainter.pth', quiet=False)

print('Downloading model for evaluating VFID metric')
gdown.download('https://github.com/sczhou/ProPainter/releases/download/v0.1.0/i3d_rgb_imagenet.pt', output='saves/i3d_rgb_imagenet.pt', quiet=False)




print('Done.')
