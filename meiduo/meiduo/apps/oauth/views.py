from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from .utils import OAuthQQ
# Create your views here.

# url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
class QQAuthURLView(APIView):
    """提供QQ登录页面网址"""

    def get(self, request):

        # 创建OAuthQQ对象
        oauth = OAuthQQ()

        # 获取QQ扫码登录页面的网址
        login_url = oauth.get_login_url()

        # 响应login_url
        return Response({'login_url':login_url})
