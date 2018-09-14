import os
import sys
import random
import tempfile
import urllib

'''
This is needed so that the script running on AWS will pick up the pre-compiled dependencies
from the packages folder
'''
current_location = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_location, 'packages'))

'''
The following imports must be placed after picking up of pre-compiled dependencies
'''
import model_inference
import gen_util

logger = gen_util.get_logger()

def predict(params):

    random_images = [
        'https://www.proplanveterinarydiets.com/media/2809/early-con-hero-desktop.jpg',
        'https://elliottbayah.com/files/2015/01/sad-pug.jpg',
        'https://epi.azureedge.net/website-images/images/default-album/dog-scratching.jpg',
        'https://www.quickanddirtytips.com/sites/default/files/images/8364/doggy.jpg.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/f/f8/Wikipedia_editor_hat_w_dog.JPG',
        'http://users.usinternet.com/nkelebay/Images/Cat_Melon.jpg',
        'https://media.treehugger.com/assets/images/2018/01/cat-cuddler.jpg',
        'https://vignette.wikia.nocookie.net/batman/images/1/19/Catwoman_Michelle_Pfeiffer.jpg',
        'http://media.gizmodo.co.uk/wp-content/uploads/2016/03/laika-620x349.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Snoop_Dogg_2012.jpg/1024px-Snoop_Dogg_2012.jpg',
        'https://cf.ltkcdn.net/sewing/images/std/163106-350x322-cat.jpg',
        'https://upload.wikimedia.org/wikipedia/en/c/c6/Puppy-sam.jpg',
        'https://fido.imgix.net/wp/2013/11/cute-puppy.jpg',
        'https://i.pinimg.com/originals/8d/32/b0/8d32b02b507394cc81428ba674dd9af3.jpg',
        ]

    image_url = random.choice(random_images)
    images_url = None
    tmp_dir = tempfile.mkdtemp() #TODO cleanup
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
    inf_dir = tmp_dir

    model_url = 'https://s3.amazonaws.com/glikson-public/DLL/model/model_16x16.hdf5'
    if 'MODEL' in os.environ:
        model_url = os.environ['MODEL']
    model_local_path = '/tmp/model.hdf5'
    if not os.path.isfile(model_local_path):
        logger.info("Downloading model '{}'".format(model_url))
        urllib.urlretrieve(model_url, model_local_path)
        logger.info("...done")
    else:
        logger.info("Using existing model file: '{}'".format(model_local_path))

    inf_res = model_inference.inference_model(
           batch_size = 32,
           image_width = 16, image_height = 16, auto_resize_images = True,
           inference_path = inf_dir,
           model_spec_filepath = model_local_path,
           choose_n_from_inference = None, random_seed = None,
           verbose = False
           )
    return image_url, inf_res

