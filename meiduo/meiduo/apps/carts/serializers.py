from rest_framework import serializers

from goods.models import SKU


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