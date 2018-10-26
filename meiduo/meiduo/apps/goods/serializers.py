from drf_haystack.serializers import HaystackSerializer
from rest_framework import serializers

from goods.search_indexes import SKUIndex
from .models import SKU


class SKUSerializer(serializers.ModelSerializer):
    """序列化器序输出商品SKU信息"""

    class Meta:
        model = SKU
        # 输出：序列化的字段
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')


class SKUIndexSerializer(HaystackSerializer):
    """
    SKU索引结果数据序列化器
    """
    object = SKUSerializer(read_only=True)

    class Meta:
        index_classes = [SKUIndex]
        fields = ('text', 'object')