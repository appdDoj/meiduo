from rest_framework import serializers

from .models import SKU


class SKUSerializer(serializers.ModelSerializer):
    """序列化器序输出商品SKU信息"""

    class Meta:
        model = SKU
        # 输出：序列化的字段
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')