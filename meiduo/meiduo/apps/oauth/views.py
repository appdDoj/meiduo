from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from rest_framework.generics import GenericAPIView

from .utils import OAuthQQ
from .exceptions import QQAPIException
from .models import OAuthQQUser
# Create your views here.


import logging
# 日志记录器
logger = logging.getLogger('django')


# url(r'^qq/user/$', views.QQAuthUserView.as_view()), 
class QQAuthUserView(GenericAPIView):

    # 指定序列化器
    serializer_class = 'QQAuthUserSerializer'

    def get(self, request):
        """
        处理oauth_callback回调页面时
        提取code,access_token,openid
        """

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
            # oauth_model : 代表一条记录，OAuthQQUser类型的对象
            oauth_model = OAuthQQUser.objects.get(openid=open_id)
        except OAuthQQUser.DoesNotExist:
            # 如果openid没绑定美多商城用户，创建用户并绑定到openid

            # 生成openid签名后的结果
            token_openid = oauth.generate_save_user_token(open_id)
            # 将openid签名之后的结果响应给用户
            return Response({'access_token': token_openid})
            # return Response({'openid':open_id})
        else:
            # 如果openid已绑定美多商城用户，直接生成JWT token，并返回
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            # 获取跟openid绑定的user对象
            user = oauth_model.user

            payload = jwt_payload_handler(user)
            # JWT token
            token = jwt_encode_handler(payload)

            # 响应数据
            return Response({
                'token':token,
                'user_id':user.id,
                'username':user.username
            })

    def post(self, request):
        """openid绑定用户"""
        # 创建序列化器
        serializer = self.get_serializer(data=request.data)
        # 校验
        serializer.is_valid(raise_exception=True)
        # 调用create方法，实现绑定用户的保存
        user = serializer.save()

        # 生成状态保持信息
        # 生成JWT token，并响应
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        return Response({
            'token': token,
            'username': user.username,
            'user_id': user.id
        })


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
