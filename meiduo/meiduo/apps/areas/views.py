from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Area
from . import serializers


# Create your views here.


class AreasViewSet(ReadOnlyModelViewSet):
    """省市区视图集
    list:
    返回省级列表数据

    retrieve:
    返回城市和区县数据
    """

    # 禁用分页效果
    pagination_class = None

    # 指定查询集
    # queryset = Area.objects.all()
    def get_queryset(self):
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    # 指定序列化器
    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.AreasSerializer
        else:
            return serializers.SubsAreasSerializer


