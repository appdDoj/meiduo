from rest_framework import serializers

from goods.models import SKU


class CartDeleteSerializer(serializers.Serializer):
    """
    删除购物车数据序列化器
    """
    sku_id = serializers.IntegerField(label='商品id', min_value=1)

    def validate_sku_id(self, value):
        try:
            sku = SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        return value


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')
    selected = serializers.BooleanField(label='是否勾选')

    class Meta:
        model = SKU
        fields = ('id', 'count', 'name', 'default_image_url', 'price', 'selected')


class CartSerializer(serializers.Serializer):
    """购物车序列化器：提供反序列化校验和序列化"""
    sku_id = serializers.IntegerField(label='商品 SKU ID', min_value=1)
    count = serializers.IntegerField(label='商品数量', min_value=1)
    selected = serializers.BooleanField(label='是否勾选', default=True)

    def validate(self, attrs):
        """对sku_id和count进行联合校验"""

        # 读取sku_id和count
        sku_id = attrs.get('sku_id')
        count = attrs.get('count')

        # 校验sku_id
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('sku_id 不存在')

        # 校验count
        if count > sku.stock:
            raise serializers.ValidationError('库存不足')

        return attrs