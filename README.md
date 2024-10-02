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
datasets [[DAVIS_modified]](https://drive.google.com/file/d/1GvLYhda18kv6iYTUxn8lWmX6-WQ6b89e/view?usp=sharing)
[[runtime_dataset]](https://drive.google.com/file/d/1nQJlLPY419vLeDgDV-7Fm386iymjwNaw/view?usp=sharing)
and the pretrained models first.

Unzip the datasets in the ```datasets``` directory. The directory should look like this:

```
datasets
   |- DAVIS_modified
        |- Annotations
        |- JPEGImages
        |- Scribbles
        |- test_masks
   |- runtime_dataset
        |- JPEGImages
        |- Scribbles
```

Run the MiVOS evaluation: (use ```--single_object``` argument to simulate scribbles drawn on a canvas,
```--eval_each_object``` can be used to reproduce the results in the MiVOS paper)

```shell
python eval_mivos.py --output mivos_eval --save_mask --single_object
```

Run the ProPainter evaluation: (use ```--bounding_box``` argument to limit the inpainting to a bounding box of the mask)

```shell
python eval_propainter.py --output propainter_eval --save_results --bounding_box
```

Run the runtime evaluation: (```--single_object``` and ```--bounding_box``` can also be used here)

```shell
python eval_runtime.py --output runtime_eval --bounding_box
```