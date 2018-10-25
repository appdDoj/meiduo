from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView

from . import serializers
from .models import User

from .serializers import CreateUserSerializer

# url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
class UsernameCountView(APIView):
    """
    手机号数量
    """
    def get(self, request, username):
        """
        获取指定手机号数量
        """
        # 判断用户名是否存在：根据用户名在数据库中做统计
        count = User.objects.filter(username=username).count()
        return Response({
            'username': username,
            'count': count
        })

# url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
class MobileCountView(APIView):
    """
    用户名数量
    """
    def get(self, request, mobile):
        """
        获取指定用户名数量
        """
        # 判断手机号是否存在：统计
        count = User.objects.filter(mobile=mobile).count()
        return Response({
            'mobile': mobile,
            'count': count
        })


class UserCreateView(CreateAPIView):
    """注册
    # 新增（用户数据-->校验-->反序列化-->create()-->save()）：保存用户传入的数据到数据库
    """
    # 指定序列化器
    serializer_class = serializers.CreateUserSerializer
