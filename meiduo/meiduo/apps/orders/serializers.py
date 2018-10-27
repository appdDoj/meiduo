from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from django_redis import get_redis_connection

from goods.models import SKU
from . models import OrderInfo, OrderGoods


class CommitOrderSerializer(serializers.ModelSerializer):
    """提交订单序列化器"""

    class Meta:
        model = OrderInfo
        # order_id ：输出；address 和 pay_method : 输入
        fields = ('order_id', 'address', 'pay_method')
        read_only_fields = ('order_id',)
        # 指定address 和 pay_method 为输出
        extra_kwargs = {
            'address': {
                'write_only': True,
            },
            'pay_method': {
                'write_only': True,
            }
        }

    def create(self, validated_data):
        """重写序列化器的create方法：
        为了能够自己写代码按照需求保存订单基本信息和订单商品信息
        """
        # 获取当前保存订单时需要的信息

        # 获取登录用户
        user = self.context['request'].user

        # 生成订单编号：20180802172710000000001 (年月日时分秒+用户id),用户id最多9位，不够9位补0
        # 获取当前时区的当前的时间 ： timezone.now()
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        # 获取validated_data里面的address和pay_method
        address = validated_data.get('address')
        pay_method = validated_data.get('pay_method')

        # 保存订单基本信息 OrderInfo（主体业务逻辑）
        # 模型类.objects.create() : 在创建模型对象的同时给属性赋值，并自动同步数据到数据库
        order = OrderInfo.objects.create(
            order_id=order_id,
            user = user,
            address = address,
            total_count = 0,
            total_amount = Decimal('0.00'),
            freight = Decimal('10.00'),
            pay_method = pay_method,  # 1(货到付款) / 2(支付宝支付)
            status = OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
            'ALIPAY'] else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        )

        # 从redis读取购物车中被勾选的商品信息
        redis_conn = get_redis_connection('cart')
        # 获取hash里面的sku_id和count
        # {
        #     b'sku_id_1':b'count_1',
        #     b'sku_id_2': b'count_2'
        # }
        redis_cart_dict = redis_conn.hgetall('cart_%s' % user.id)

        # 获取set里面的sku_id
        # [b'sku_id_1']
        redis_cart_selected = redis_conn.smembers('selected_%s' % user.id)

        # 读取出被勾选的商品的信息
        # {
        #     sku_id_1: count_1
        # }
        carts = {}
        for sku_id in redis_cart_selected:
            carts[int(sku_id)] = int(redis_cart_dict[sku_id])

        # 读取出carts里面所有的sku_id
        sku_ids = carts.keys()

        # 遍历购物车中被勾选的商品信息
        for sku_id in sku_ids:
            # 获取sku对象
            sku = SKU.objects.get(id=sku_id)

            # 判断库存 
            cart_sku_count = carts[sku.id]
            if cart_sku_count > sku.stock:
                raise serializers.ValidationError('库存不足')

            # 减少库存，增加销量 SKU 
            # sku.stock = sku.stock - cart_sku_count
            # sku.sales = sku.sales + cart_sku_count
            sku.stock -= cart_sku_count
            sku.sales += cart_sku_count
            sku.save() # 同步到数据库

            # 修改SPU销量
            sku.goods.sales += cart_sku_count
            sku.goods.save() # 同步到数据库

            # 保存订单商品信息 OrderGoods（主体业务逻辑）
            OrderGoods.objects.create(
                order=order,
                sku = sku,
                count = cart_sku_count,
                price = sku.price,
            )

            # 累加计算总数量和总价
            order.total_count += cart_sku_count
            order.total_amount += (cart_sku_count * sku.price)

        # 最后加入邮费和保存订单信息
        order.total_amount += order.freight
        order.save()

        # 清除购物车中已结算的商品(暂时不做，当把订单提交做完再清空购物车，避免每次测试结束都要新加购物车)

        # 返回新建的资源对象
        return order


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)