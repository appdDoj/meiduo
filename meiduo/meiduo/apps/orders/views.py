from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_redis import get_redis_connection
from rest_framework.response import Response
from decimal import Decimal
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.exceptions import PermissionDenied

from goods.models import SKU
from .serializers import OrderSettlementSerializer, SaveOrderSerializer, OrderInfoSerializer
from .serializers import SaveOrderCommentSerializer, OrderGoodsSerializer
from .models import OrderInfo, OrderGoods
# Create your views here.


class OrderSettlementView(APIView):
    """
    订单结算
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取
        """
        user = request.user

        # 从购物车中获取用户勾选要结算的商品信息
        redis_conn = get_redis_connection('cart')
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

        cart = {}
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(redis_cart[sku_id])

        # 查询商品信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]

        # 运费
        freight = Decimal('10.00')

        serializer = OrderSettlementSerializer({'freight': freight, 'skus': skus})
        return Response(serializer.data)


# 上课时讲解，只有保存订单，未包含查询我的订单信息部分
class SaveOrderView(CreateAPIView):
    """
    保存订单
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SaveOrderSerializer


class OrderViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, GenericViewSet):
    """
    订单， 包含保存订单和查询我的订单
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return SaveOrderSerializer
        else:
            return OrderInfoSerializer

    def get_queryset(self):
        user = self.request.user
        return OrderInfo.objects.filter(user=user).order_by('-create_time')


class UncommentOrderGoodsView(ListAPIView):
    """
    待评论的订单商品
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderGoodsSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        order_id = self.kwargs['order_id']
        try:
            OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            raise PermissionDenied

        return OrderGoods.objects.filter(order_id=order_id, is_commented=False)


class OrderCommentView(CreateAPIView):
    """
    订单评论
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = SaveOrderCommentSerializer

