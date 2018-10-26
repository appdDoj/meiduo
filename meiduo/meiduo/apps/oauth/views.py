from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .utils import OAuthQQ
from .exceptions import QQAPIException
from .models import OAuthQQUser
# Create your views here.


import logging
# 日志记录器
logger = logging.getLogger('django')


# url(r'^qq/user/$', views.QQAuthUserView.as_view()), 
class QQAuthUserView(APIView):
    """
    处理oauth_callback回调页面时
    提取code,access_token,openid
    """

    def get(self, request):
        # 提取code请求参数
        code = request.query_params.get('code')
        if code is None:
            return Response({'message':'缺少code'}, status=status.HTTP_400_BAD_REQUEST)

        # 创建OAuthQQ对象
        oauth = OAuthQQ()

        try:
            # 使用code向QQ服务器请求access_token
            access_token = oauth.get_access_token(code)

            # 使用access_token向QQ服务器请求openid
            open_id = oauth.get_open_id(access_token)
        except QQAPIException as e:
            logger.error(e)
            return Response({'message': 'QQ服务异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 使用openid查询该QQ用户是否在美多商城中绑定过用户
        try:
            OAuthQQUser.objects.get(openid=open_id)
        except OAuthQQUser.DoesNotExist:
            # 如果openid没绑定美多商城用户，创建用户并绑定到openid
            pass
        else:
            # 如果openid已绑定美多商城用户，直接生成JWT token，并返回
            pass


# url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
class QQAuthURLView(APIView):
    """提供QQ登录页面网址
    http://127.0.0.1:8000/oquth/qq/authorization/?next=user_center_info.html
    """

    def get(self, request):

        # 获取next参数
        next = request.query_params.get('next')

        # 创建OAuthQQ对象
        oauth = OAuthQQ(state=next)

        # 获取QQ扫码登录页面的网址
        login_url = oauth.get_login_url()

        # 响应login_url
        return Response({'login_url':login_url})
