import os
import sys
import json
from django.http import HttpResponse

import tensorflow as tf
from dogcat import inference, gen_util

logger = gen_util.get_logger()

def predict_json(response):
    try:
        _,inf_res = inference.predict(response.GET)
        return HttpResponse(json.dumps({"inference":inf_res}), content_type='application/json')
    except Exception as ex:
        logger.error('Error: '+str(ex))
        return HttpResponse(json.dumps({"error":str(ex)}), content_type='application/json')


def predict_html(response):
    # Construct resulting HTML
    body = '<!DOCTYPE html><html> <link rel="icon" type="image/png" href="https://s3.amazonaws.com/glikson-public/DLL/images/favicon.png">'
    body += '<body><a href=\"?\"><h1>Cats vs Dogs Classification</h1></a>'
    body += '<p>Enter URL of an image with a dog or a cat:</p>'
    body += '<form method=\"get\"> <input type=\"text\" name=\"image\" size=\"100\"> <input type=\"submit\" value=\"Submit\"></form><br><p>'

    try:
        image_url, inf_res = inference.predict(response.GET)
    except Exception as ex:
        logger.error('Error: '+str(ex))
        body += 'Error:<br><pre>{}</pre>'.format(str(ex))
    else:
        if image_url is not None:
            prob = float(int(float(inf_res[0][1])*1000+0.5))/10
            if prob>50:
                body += '<img src=\"{}\" width=\"400\"><br>I am {}% sure this is a dog.'.format(image_url, prob)
            else:
                body += '<img src=\"{}\" width=\"400\"><br>I am {}% sure this is a cat.'.format(image_url, 100-prob)
    body += '<hr><p>Note: remove <i>.html</i> from the URL and add (or keep) <i>?image=IMAGE_URL</i> to use the JSON interface.</p></body></html>'
    return HttpResponse(body, content_type='text/html')

def error404(request):
    # NOTE: we intentionally do not return an error code here
    return HttpResponse(json.dumps({"message":"use ${hostname}/dev/predict.html to check the web service"}), content_type='application/json')
