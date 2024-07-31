# VideoInpainter

## Prerequisites

To install PyTorch look up the command on pytorch.org. Installation for pytorch with CUDA 11.8:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

Install requirements:

```bash
pip install -r requirements.txt
```

Download the models:

```bash
python download_models.py
```

## Installation

1. Clone the project:

```bash
git clone https://github.com/Lim-Kevin/VideoInpainter
```

2. Initialize and pull submodules:

```bash
git submodule update --init -recursive
```

## Running the app

Run the app (this will execute app.py):

```bash
flask run
```

Run with debugging enabled:

```bash
flask run --debug
```

## Evaluation:

Make sure to download the
dataset [[Google Drive]](https://drive.google.com/file/d/1aNoIMRuOxqJjPaQQdjZ3Vo_2PODs9GXy/view?usp=drive_link) and the
pretrained models first.

Unzip the ```dataset``` in the dataset directory.

Run the MiVOS evaluation: (use ```--one_object``` argument to simulate scribbles drawn on a canvas)
```bash
python lib/MiVOS_STCN/eval_interactive_davis.py --output mivos_eval --save_mask --one_object
```

