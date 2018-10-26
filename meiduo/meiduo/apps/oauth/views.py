from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from .utils import OAuthQQ
# Create your views here.


# url(r'^qq/user/$', views.QQAuthUserView.as_view()), 
class QQAuthUserView(APIView):
    """
    处理oauth_callback回调页面时
    提取code,access_token,openid
    """

    def get(self, request):
        # 提取code请求参数
        # 使用code向QQ服务器请求access_token
        # 使用access_token向QQ服务器请求openid
        # 使用openid查询该QQ用户是否在美多商城中绑定过用户


        # 如果openid已绑定美多商城用户，直接生成JWT token，并返回
        # 如果openid没绑定美多商城用户，创建用户并绑定到openid
        pass


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
