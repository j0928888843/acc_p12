import pathlib
import logging
import sys

import numpy as np
import tensorflow as tf
from PIL import Image

def get_all_files_in_dir(dir_path):
    """
    Gets all files in a directory.
    This function is not recursive and therefore it does not search
    subdirectories.
    """
    dir_handle = pathlib.Path(dir_path)
    assert(dir_handle.is_dir())
    # Non-recursive
    found_path_files = [f.resolve() for f in dir_handle.iterdir() if f.is_file()]
    return found_path_files

def get_and_choose_n_files_in_dir(dir_path, choose_n):
    """
    Gets all files in a directory and returns choose_n of them.
    Returns all files if choose_n is none.
    This function is not recursive and therefore it does not search
    subdirectories.
    """
    path_files = get_all_files_in_dir(dir_path)
    if choose_n is not None:
        path_files = np.random.choice(
                path_files,
                choose_n,
                replace=False)
    return path_files

def load_images(path_files, image_width, image_height):
    """
    Returns numpy representation of images
    """
    imgs_arr = []
    for f in path_files:
        # From
        # https://stackoverflow.com/questions/13550376/pil-image-to-array-numpy-array-to-array-python
        with Image.open(f.absolute()) as img:
            img = img.resize((image_width, image_height), Image.ANTIALIAS)
            img_arr = np.fromstring(img.tobytes(), dtype=np.uint8)
            img_arr = img_arr.reshape((img.size[1], img.size[0], 3))
            imgs_arr.append(img_arr)
    return np.array(imgs_arr)

def setup_logger():
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s'))
    logger = logging.getLogger('lambda')
    logger.addHandler(h)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger

logger = setup_logger()

def get_logger():
    return logger

