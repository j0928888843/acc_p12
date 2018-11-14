import numpy as np
import tensorflow as tf
import time
import h5py # We don't call this directly but needed for keras
import argparse
import random
import pprint
import operator

import gen_util

logger = gen_util.get_logger()

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

def argparse_inference_handler(args):
    """
    Runs model training for command line
    """
    batch_size = args.batch_size
    image_width = args.image_width
    image_height = args.image_height
    inference_path = args.inference_path
    model_spec_filepath = args.model_spec_filepath
    choose_n_from_inference = args.choose_n_from_inference
    random_seed = args.random_seed
    verbose = args.verbose
    auto_resize_images = args.auto_resize_images

    return inference_model(
        batch_size=batch_size,
        image_width=image_width,
        image_height=image_height,
        inference_path=inference_path,
        model_spec_filepath=model_spec_filepath,
        choose_n_from_inference=choose_n_from_inference,
        random_seed=random_seed,
        verbose=verbose,
        auto_resize_images=auto_resize_images)

def create_inference_model(
        model_spec_filepath,
        random_seed,
        verbose,
        ):
    """
    Constructor for inference model
    """
    logger.info("Initializing the model...")
    if random_seed is not None:
        random.seed(random_seed)
        np.random.seed(random_seed)
        tf.set_random_seed(random_seed)
    inf_model = tf.keras.models.load_model(model_spec_filepath)
    logger.info("...done")
    if verbose:
        inf_model.summary()
    return inf_model

def run_inference_model(
        inf_model,
        batch_size,
        image_width,
        image_height,
        inference_path,
        choose_n_from_inference,
        verbose,
        auto_resize_images):
    """
    Runs model training
    """
    logger.info("Loading images")
    if auto_resize_images:
        image_height, image_width, _ = get_model_input_shape(inf_model)

    inference_path_files = gen_util.get_all_files_in_dir(inference_path)
    if choose_n_from_inference is not None:
        inference_path_files = np.random.choice(
                inference_path_files,
                choose_n_from_inference,
                replace=False)
    inference_path_filenames = list(map(lambda x : x.as_posix(), inference_path_files))
    inference_X = gen_util.load_images(
            path_files=inference_path_files,
            image_width=image_width,
            image_height=image_height,
            )
    logger.info("Calculating prediction...")
    train_y = inf_model.predict(inference_X, batch_size=batch_size, verbose=1)
    logger.info("...done")

    file_to_pred = [(f.name, p[0]) for f, p in zip(inference_path_files, train_y.tolist())]
    sorted_file_to_pred = sorted(file_to_pred, key=operator.itemgetter(0))
    print("Prediction (probability of dog):\n'{}'".format(pprint.pformat(sorted_file_to_pred)))
    return sorted_file_to_pred

initialized = False
inf_model = None
used_model_spec_filepath = None

def inference_model(
    batch_size,
    image_width,
    image_height,
    inference_path,
    model_spec_filepath,
    choose_n_from_inference,
    random_seed,
    verbose,
    auto_resize_images):
    """
    Creates model lazily and runs model training
    """
    global initialized
    global inf_model
    global used_model_spec_filepath

    if not initialized or used_model_spec_filepath != model_spec_filepath:
        inf_model = create_inference_model(model_spec_filepath,
                                           random_seed,
                                           verbose)
        initialized = True
        used_model_spec_filepath = model_spec_filepath

    sorted_file_to_pred = run_inference_model(
            inf_model,
            batch_size,
            image_width,
            image_height,
            inference_path,
            choose_n_from_inference,
            verbose,
            auto_resize_images)

    return sorted_file_to_pred

def setup_inference_subparser(inference_subparser):
    inference_subparser.add_argument(
            "model_spec_filepath",
            type=str,
            help="The trained Keras model to use for inference."
            )
    inference_subparser.add_argument(
            "--batch_size",
            default=32,
            type=int,
            help="The batch size to use."
            )
    inference_subparser.add_argument(
            "--image_width",
            default=16,
            type=int,
            help="The pixel width to resize images to",
            )
    inference_subparser.add_argument(
            "--image_height",
            default=16,
            type=int,
            help="The pixel height to resize images to",
            )
    inference_subparser.add_argument(
            "--inference_path",
            default="./data/inf/",
            type=str,
            help="The path to the directory with input images for inference."
            )
    inference_subparser.add_argument(
            "--random_seed",
            default=None,
            type=int,
            help="The random seed to initialize systems with."
                 " This does not cover all source of randomness."
            )
    inference_subparser.add_argument(
            "--choose_n_from_inference",
            default=None,
            type=int,
            help="The amount of random samples to choose from the inference set"
            )
    inference_subparser.add_argument(
            "--auto_resize_images",
            action="store_true",
            help="Determine image width/height from model input."
            )
    inference_subparser.set_defaults(func=argparse_inference_handler)
    return inference_subparser

