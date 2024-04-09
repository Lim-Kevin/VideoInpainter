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