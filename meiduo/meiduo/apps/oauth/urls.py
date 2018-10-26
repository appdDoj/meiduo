from django.conf.urls import url

from . import views


urlpatterns = [
    # 提供用户登录到QQ的网址
    url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
]