from django.shortcuts import render
from drf_haystack.viewsets import HaystackViewSet
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView

from .models import SKU
from . import serializers
# Create your views here.


class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]

    serializer_class = serializers.SKUIndexSerializer


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