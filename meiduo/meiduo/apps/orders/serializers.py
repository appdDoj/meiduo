from rest_framework import serializers
from django_redis import get_redis_connection
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import logging

from goods.models import SKU
from .models import OrderInfo, OrderGoods


logger = logging.getLogger('django')


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


class SaveOrderSerializer(serializers.ModelSerializer):
    """
    下单数据序列化器
    """
    class Meta:
        model = OrderInfo
        # order_id ：输出；address 和 pay_method : 输入
        fields = ('order_id', 'address', 'pay_method')
        read_only_fields = ('order_id',)
        # 指定address 和 pay_method 为输出
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        """重写序列化器的create方法：
        为了能够自己写代码按照需求保存订单基本信息和订单商品信息
        """
        # 获取当前保存订单时需要的信息
        # 获取当前下单用户
        user = self.context['request'].user

        # 组织订单编号 20170903153611+user.id(年月日时分秒+用户id),用户id最多9位，不够9位补0
        # timezone.now() -> datetime
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
        # 获取validated_data里面的address和pay_method
        address = validated_data['address']
        pay_method = validated_data['pay_method']

        # 生成订单
        with transaction.atomic():
            # 在with语句一开始的地方，创建一个保存点，用于回滚或者提交到此
            save_id = transaction.savepoint()

            # 全部try一下，一旦有错，暴力回滚
            try:
                # 创建订单信息
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal(0),
                    freight=Decimal(10),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH'] else OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )

                # 获取购物车信息
                # 从redis读取购物车中被勾选的商品信息
                redis_conn = get_redis_connection("cart")
                # 获取hash里面的sku_id和count
                # {
                #     b'sku_id_1':b'count_1',
                #     b'sku_id_2': b'count_2'
                # }
                redis_cart = redis_conn.hgetall("cart_%s" % user.id)
                # 获取set里面的sku_id
                # [b'sku_id_1']
                cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)
                # 读取出被勾选的商品的信息
                # {
                #     sku_id_1: count_1
                # }
                # 将bytes类型转换为int类型
                cart = {}
                for sku_id in cart_selected:
                    cart[int(sku_id)] = int(redis_cart[sku_id])

                # # 一次查询出所有商品数据
                # skus = SKU.objects.filter(id__in=cart.keys())

                # 处理订单商品
                sku_id_list = cart.keys()
                for sku_id in sku_id_list:
                    while True:
                        sku = SKU.objects.get(id=sku_id)

                        sku_count = cart[sku.id]

                        # 判断库存
                        origin_stock = sku.stock  # 原始库存
                        origin_sales = sku.sales  # 原始销量

                        if sku_count > origin_stock:
                            transaction.savepoint_rollback(save_id)
                            raise serializers.ValidationError('商品库存不足')

                        # 用于演示并发下单
                        # import time
                        # time.sleep(5)

                        # 减少库存
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count

                        # 根据原始库存条件更新，返回更新的条目数，乐观锁
                        ret = SKU.objects.filter(id=sku.id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                        if ret == 0:
                            continue

                        # 累计商品的SPU 销量信息
                        sku.goods.sales += sku_count
                        sku.goods.save()

                        # 累计订单基本信息的数据
                        order.total_count += sku_count  # 累计总金额
                        order.total_amount += (sku.price * sku_count)  # 累计总额

                        # 保存订单商品
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )

                        # 更新成功
                        break

                # 更新订单的金额数量信息
                order.total_amount += order.freight
                order.save()

            except serializers.ValidationError:
                # 不需要回滚，因为在抛出该异常之前，已经回滚了
                # 捕获自己抛出的异常信息
                raise
            except Exception as e:
                # 暴力回滚
                logger.error(e)
                transaction.savepoint_rollback(save_id)
                raise # 捕获到什么异常自动的抛出什么异常，没有必要再去给异常起别名

            # 提交事务
            transaction.savepoint_commit(save_id)

            # 更新redis中保存的购物车数据
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, *cart_selected)
            pl.srem('cart_selected_%s' % user.id, *cart_selected)
            pl.execute()
            return order


class SKUSerializer(serializers.ModelSerializer):
    """
    SKU商品数据序列化器
    """
    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url')


class OrderGoodsSerializer(serializers.ModelSerializer):
    """
    订单商品数据序列化器
    """
    sku = SKUSerializer()

    class Meta:
        model = OrderGoods
        fields = ('id', 'sku', 'count', 'price')


class DateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        tz = timezone.get_default_timezone()
        value = timezone.localtime(value, timezone=tz)
        return super().to_representation(value)


class OrderInfoSerializer(serializers.ModelSerializer):
    """
    订单数据序列化器
    """
    skus = OrderGoodsSerializer(many=True)
    create_time = DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = OrderInfo
        fields = ('order_id', 'create_time', 'total_amount', 'freight', 'status', 'skus', 'pay_method')


class SaveOrderCommentSerializer(serializers.ModelSerializer):
    """
    保存订单评论数据序列化器
    """
    class Meta:
        model = OrderGoods
        fields = ('sku', 'comment', 'score', 'is_anonymous')
        extra_kwargs = {
            'comment': {
                'required': True
            },
            'score': {
                'required': True
            },
            'is_anonymous': {
                'required': True
            }
        }

    def validate(self, datas):
        order_id = self.context['view'].kwargs['order_id']
        user = self.context['request'].user
        try:
            OrderInfo.objects.filter(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
        except OrderInfo.DoesNotExist:
            raise serializers.ValidationError('订单信息有误')

        return datas

    @transaction.atomic
    def create(self, validated_data):
        order_id = self.context['view'].kwargs['order_id']
        sku = validated_data['sku']

        # 保存评论数据
        OrderGoods.objects.filter(order_id=order_id, sku=sku, is_commented=False).update(
            comment=validated_data['comment'],
            score=validated_data['score'],
            is_anonymous=validated_data['is_anonymous'],
            is_commented=True
        )

        # 累计评论数据
        sku.comments += 1
        sku.save()
        sku.goods.comments += 1
        sku.goods.save()

        # 如果所有订单商品都已评价，则修改订单状态为已完成
        if OrderGoods.objects.filter(order_id=order_id, is_commented=False).count() == 1:
            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM['FINISHED'])

        return validated_data






