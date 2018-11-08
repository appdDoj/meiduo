from django.shortcuts import render
from rest_framework.generics import ListAPIView, GenericAPIView
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from drf_haystack.viewsets import HaystackViewSet
from rest_framework_extensions.cache.mixins import ListCacheResponseMixin

from . import constants
from .serializers import SKUSerializer, ChannelSerializer, CategorySerializer, SKUIndexSerializer, SKUCommentSerializer

from meiduo.utils.pagination import StandardResultsSetPagination
from .models import SKU, GoodsCategory

from orders.models import OrderGoods
from . import serializers

class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]

    # serializer_class = serializers.SKUIndexSerializer
    serializer_class = SKUIndexSerializer

    pagination_class = StandardResultsSetPagination

# url(r'^categories/(?P<category_id>\d+)/skus/', views.SKUListView.as_view()),
class SKUListView(ListAPIView):
    """商品列表"""

    # 指定查询集
    # queryset = SKU.objects.all()

    # 指定序列化器
    serializer_class = serializers.SKUSerializer

    # 指定排序后端
    filter_backends = [OrderingFilter]
    # 指定排序字段:字段名字必须和模型属性同名，不需要在这里指定是否倒叙
    ordering_fields = ('create_time', 'price', 'sales')

    def get_queryset(self):
        # 从视图对象的kwargs属性中读取路径参数
        category_id = self.kwargs.get('category_id')
        # category_id 对sku数据进行过滤，保持查询到的sku信息都是指定的category_id所在的分类
        return SKU.objects.filter(category_id=category_id, is_launched=True)

class CategoryView(GenericAPIView):
    """
    类别
    """
    queryset = GoodsCategory.objects.all()

    def get(self, request, pk=None):
        ret = dict(
            cat1='',
            cat2='',
            cat3=''
        )
        category = self.get_object()
        if category.parent is None:
            # 当前类别为一级类别
            ret['cat1'] = ChannelSerializer(category.goodschannel_set.all()[0]).data
        elif category.goodscategory_set.count() == 0:
            # 当前类别为三级
            ret['cat3'] = CategorySerializer(category).data
            cat2 = category.parent
            ret['cat2'] = CategorySerializer(cat2).data
            ret['cat1'] = ChannelSerializer(cat2.parent.goodschannel_set.all()[0]).data
        else:
            # 当前类别为二级
            ret['cat2'] = CategorySerializer(category).data
            ret['cat1'] = ChannelSerializer(category.parent.goodschannel_set.all()[0]).data

        return Response(ret)




class HotSKUListView(ListCacheResponseMixin, ListAPIView):
    """
    热销商品, 使用缓存扩展
    """
    serializer_class = SKUSerializer
    pagination_class = None

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:constants.HOT_SKUS_COUNT_LIMIT]


class SKUCommentsListView(ListCacheResponseMixin, ListAPIView):
    """
    商品评论
    """
    serializer_class = SKUCommentSerializer
    pagination_class = None

    def get_queryset(self):
        sku_id = self.kwargs['sku_id']
        queryset = OrderGoods.objects.filter(sku_id=sku_id, is_commented=True).order_by('-update_time')[:constants.SKU_COMMENT_COUNT_LIMIT]

        for order_goods in queryset:
            username = order_goods.order.user.username
            if order_goods.is_anonymous:
                order_goods.username = username[0] + '***' + username[-1]
            else:
                order_goods.username = username

        return queryset
