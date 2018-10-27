from django.shortcuts import render
from rest_framework.views import APIView

from . import serializers


# Create your views here.


class CartView(APIView):
    """购物车增、查、改、删

    用户不登录可以访问该接口：不传入JWT token，不指定权限
    用户登录也可以访问该接口：必须传入JWT token，必须指定权限

    用户登录和未登录都可以访问该接口：
        不能指定权限，保证未登录用户可以访问
        必须传入JWT token，保证登录用户可以是被身份
    """

    def perform_authentication(self, request):
        """重写执行认证方法的目的：取消视图的认证，是为了保证用户登录或未登录都可以进入到视图内部
        可以避免用户未登录，但是传入了JWT token时，在认证过程中报401的错误
        """
        pass

    def post(self, request):
        """添加购物车"""
        # 创建序列化器，校验参数，并返回校验之后的参数
        serializer = serializers.CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 如果是已登录用户，存储购物车到redis
            pass
        else:
            # 如果是未登录用户，存储购物车到cookie
            pass

    def get(self, request):
        """读取购物车"""
        pass

    def put(self, request):
        """修改购物车"""
        pass

    def delete(self, request):
        """删除购物车"""
        pass
