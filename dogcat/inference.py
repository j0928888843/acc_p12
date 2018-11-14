import numpy as np
import tensorflow as tf
import time
import h5py # We don't call this directly but needed for keras
import random
import pprint
import operator

import os
import sys
import shutil
import tempfile
import urllib

import gen_util

logger = gen_util.get_logger()

inf_model = None

def get_model_input_shape(model):
    """
    Gets the dimensions of a sequential keras model's input.
    This assumes an image input.
    """
    assert len(model.inputs) == 1, "Only supporting 1 input into model"
    model_input = model.inputs[0]
    # TODO Assumes channel last and conv layer
    _, image_height, image_width, image_channel = model_input.shape
    return image_height, image_width, image_channel

def initialize_model(verbose):
    """
    Constructor for inference model
    """
    global inf_model
    if inf_model is None:
        model_path = "/tmp/model.hdf5"
        logger.info("Initializing the model from %s..." % model_path)
        inf_model = tf.keras.models.load_model(model_path)
        logger.info("...done")
    else:
        logger.info("Model already initialized")
    if verbose:
        inf_model.summary()

    return inf_model

def run_inference( inference_path, verbose ):
    """
    Runs model training
    """
    global inf_model
    logger.info("Loading images")
    image_height, image_width, _ = get_model_input_shape(inf_model)

    inference_path_files = gen_util.get_all_files_in_dir(inference_path)
    inference_path_filenames = list(map(lambda x : x.as_posix(), inference_path_files))
    inference_X = gen_util.load_images(
            path_files=inference_path_files,
            image_width=image_width,
            image_height=image_height,
            )
    logger.info("Calculating prediction...")
    train_y = inf_model.predict(inference_X, batch_size=32, verbose=1)
    logger.info("...done")

    file_to_pred = [(f.name, p[0]) for f, p in zip(inference_path_files, train_y.tolist())]
    sorted_file_to_pred = sorted(file_to_pred, key=operator.itemgetter(0))
    print("Prediction (probability of dog):\n'{}'".format(pprint.pformat(sorted_file_to_pred)))
    return sorted_file_to_pred

def predict(params):

    random_images = [
        'https://www.proplanveterinarydiets.com/media/2809/early-con-hero-desktop.jpg',
        'https://elliottbayah.com/files/2015/01/sad-pug.jpg',
        'https://epi.azureedge.net/website-images/images/default-album/dog-scratching.jpg',
        'https://www.quickanddirtytips.com/sites/default/files/images/8364/doggy.jpg.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/f/f8/Wikipedia_editor_hat_w_dog.JPG',
        'https://media.treehugger.com/assets/images/2018/01/cat-cuddler.jpg',
        'http://media.gizmodo.co.uk/wp-content/uploads/2016/03/laika-620x349.jpg',
        'https://cf.ltkcdn.net/sewing/images/std/163106-350x322-cat.jpg',
        'https://upload.wikimedia.org/wikipedia/en/c/c6/Puppy-sam.jpg',
        'https://fido.imgix.net/wp/2013/11/cute-puppy.jpg',
        'https://i.pinimg.com/originals/8d/32/b0/8d32b02b507394cc81428ba674dd9af3.jpg',
        ]

    image_url = random.choice(random_images)
    images_url = None
    tmp_dir = tempfile.mkdtemp()
    if params is not None:
        if 'image' in params:
            image_url = params['image']
        elif 'images' in params:
            images_url = params['images']
    if images_url is not None: # input is a tar.gz of images
        logger.info("Downloading and extracting images from '{}'".format(images_url))
        os.system("curl -sSo- {} | tar xvz -C {}".format(images_url,tmp_dir)) #TODO implement in Python
    else:
        logger.info("Retrieving image: '{}'".format(image_url))
        #TODO add error handling
        filename = image_url[image_url.rfind("/")+1:]
        local_image_path,_ = urllib.urlretrieve(image_url,os.path.join(tmp_dir,filename))
        logger.info("Retrieved image file: '{}' --> '{}'.".format(image_url,local_image_path))

    global inf_model

    if inf_model is None:
        initialize_model(verbose=False)

    inf_res = run_inference(inference_path=tmp_dir, verbose=False)

    shutil.rmtree(tmp_dir)

    return image_url, inf_res

