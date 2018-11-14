from django.conf.urls import url
import handle

urlpatterns = [
    url(r'^predict.html$', handle.predict_html, name='predict_html'),
    url(r'^predict$', handle.predict_json, name='predict_json'),
]
