from django.conf.urls import url
import handle

handler404 = handle.error404

urlpatterns = [
    url(r'^dev/predict.html$', handle.predict_html, name='predict_html'),
    url(r'^dev/predict$', handle.predict_json, name='predict_json'),
]
