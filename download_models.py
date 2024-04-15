import os
import gdown

os.makedirs('saves', exist_ok=True)

# Scribble_to_Mask model
print('Downloading s2m model...')
gdown.download('https://drive.google.com/uc?id=1HKwklVey3P2jmmdmrACFlkXtcvNxbKMM', output='saves/s2m.pth', quiet=False)

# Mask_Propagation model
print('Downloading propagation model...')
gdown.download('https://drive.google.com/uc?id=19dfbVDndFkboGLHESi8DGtuxF1B21Nm8', output='saves/propagation_model.pth', quiet=False)

# ProPainter models
print('Downloading RAFT model')
gdown.download('https://github.com/sczhou/ProPainter/releases/download/v0.1.0/raft-things.pth', output='saves/raft_things.pth', quiet=False)

print('Downloading flow competition model')
gdown.download('https://github.com/sczhou/ProPainter/releases/download/v0.1.0/recurrent_flow_completion.pth', output='saves/recurrent_flow_completion.pth', quiet=False)


print('Downloading ProPainter model')
gdown.download('https://github.com/sczhou/ProPainter/releases/download/v0.1.0/ProPainter.pth', output='saves/ProPainter.pth', quiet=False)



print('Done.')
