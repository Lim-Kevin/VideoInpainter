import os
import gdown

os.makedirs('saves', exist_ok=True)

# Scribble_to_Mask model
print('Downloading s2m model...')
gdown.download('https://drive.google.com/uc?id=1HKwklVey3P2jmmdmrACFlkXtcvNxbKMM', output='saves/s2m.pth', quiet=False)

# Mask_Propagation model
print('Downloading propagation model...')
gdown.download('https://drive.google.com/uc?id=19dfbVDndFkboGLHESi8DGtuxF1B21Nm8', output='saves/propagation_model.pth', quiet=False)

print('Done.')