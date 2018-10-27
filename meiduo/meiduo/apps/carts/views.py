from django.shortcuts import render
from rest_framework.views import APIView
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework import status
import base64
import pickle

from . import serializers
from goods.models import SKU


# Create your views here.


class CartView(APIView):
    """购物车增、查、改、删

    用户不登录可以访问该接口：不传入JWT token，不指定权限
    用户登录也可以访问该接口：必须传入JWT token，必须指定权限

    用户登录和未登录都可以访问该接口：
        不能指定权限，保证未登录用户可以访问
        必须传入JWT token，保证登录用户可以是被身份
    """

    def perform_authentication(self, request):
        """重写执行认证方法的目的：取消视图的认证，是为了保证用户登录或未登录都可以进入到视图内部
        可以避免用户未登录，但是传入了JWT token时，在认证过程中报401的错误
        """
        pass

    def post(self, request):
        """添加购物车"""
        # 创建序列化器，校验参数，并返回校验之后的参数
        serializer = serializers.CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 如果是已登录用户，存储购物车到redis
            # 创建连接到redis的对象
            redis_conn = get_redis_connection('cart')

            # 管道
            pl = redis_conn.pipeline()

            # 将sku_id和count写入到hash
            # hincrby ：自动实现自增量，会自动的判断sku_id，是否已经存在，如果存在就使用count累加原有值；反之，就赋新值
            # redis_conn.hincrby('cart_%s' % user.id, sku_id, count)
            pl.hincrby('cart_%s' % user.id, sku_id, count)

            # 将sku_id写入到set
            # redis_conn.sadd('selected_%s' % user.id, sku_id)
            pl.sadd('selected_%s' % user.id, sku_id)

            # 记住要execute
            pl.execute()

            # 响应:序列化之后的结果
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # 如果是未登录用户，存储购物车到cookie
            # 读取出cookie中原有的购物车数据
            cookie_cart_str = request.COOKIES.get('cart')

            # 判断cookie中的购物车数据是否存在，如果存在再转字典；反之，给空字典
            if cookie_cart_str:
                cookie_cart_str_bytes = cookie_cart_str.encode()
                cookie_cart_dict_bytes = base64.b64decode(cookie_cart_str_bytes)
                cookie_cart_dict = pickle.loads(cookie_cart_dict_bytes)
            else:
                cookie_cart_dict = {}

            # 判断sku_id是都在cookie_cart_dict，如果在就用新的count累加原有count;反之赋新值
            if sku_id in cookie_cart_dict:
                origin_count = cookie_cart_dict[sku_id]['count']
                count += origin_count

            cookie_cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 生成新的购物车字符串
            new_cookie_cart_dict_bytes = pickle.dumps(cookie_cart_dict)
            new_cookie_cart_str_bytes = base64.b64encode(new_cookie_cart_dict_bytes)
            new_cookie_cart_str = new_cookie_cart_str_bytes.decode()

            # 构造响应对象
            response = Response(serializer.data, status=status.HTTP_201_CREATED)

            # 将新的字典转成新的购物车字符串，写入到cookie
            response.set_cookie('cart', new_cookie_cart_str)

            # 响应
            return response

    def get(self, request):
        """读取购物车"""
        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 如果是已登录用户，存储购物车到redis
            # 创建连接到redis的对象
            redis_conn = get_redis_connection('cart')
            # 查询hash里面的所有的sku_id和count数据
            # {
            #     b'sku_id_1':b'count_1',
            #     b'sku_id_2': b'count_2',
            # }
            redis_cart_dict = redis_conn.hgetall('cart_%s' % user.id)

            # 查询set里面的所有的sku_id
            # [b'sku_id_1']
            redis_selected_set = redis_conn.smembers('selected_%s' % user.id)

            # """
            # {
            #     sku_id10: {
            #         "count": 10,  // 数量
            #         "selected": True  // 是否勾选
            #     },
            #     sku_id20: {
            #         "count": 20,
            #         "selected": False
            #     },
            #     ...
            # }
            # """
            # 准备新的购物车数据的字典，跟cookie中的购物车统一数据结构（因为cookie中的购物车数据结构便于查询sku）
            cart_dict = {}
            # 遍历redis_cart_dict，取出里面的sku_id和count,转移到cart_dict
            for sku_id, count in redis_cart_dict.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_selected_set  # 如果hash里面的sku_id不在集合中，表示未勾选，False
                }

        else:
            # 如果是未登录用户，存储购物车到cookie
            # 读取出cookie中原有的购物车数据
            cookie_cart_str = request.COOKIES.get('cart')

            # 判断cookie中的购物车数据是否存在，如果存在再转字典；反之，给空字典
            if cookie_cart_str:
                cookie_cart_str_bytes = cookie_cart_str.encode()
                cookie_cart_dict_bytes = base64.b64decode(cookie_cart_str_bytes)
                cart_dict = pickle.loads(cookie_cart_dict_bytes)
            else:
                cart_dict = {}

        # 读取出所有的购物车商品的sku_id
        sku_ids = cart_dict.keys()
        # 根据sku_ids，查询出所有的sku对象
        skus = SKU.objects.filter(id__in=sku_ids)

        # 将count和selected临时的设置给sku
        for sku in skus:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        # 序列化skus
        serializer = serializers.CartSKUSerializer(skus, many=True)

        # 响应序列化结果
        return Response(serializer.data)

    def put(self, request):
        """修改购物车"""
        # 创建序列化器，校验参数，并返回校验之后的参数
        serializer = serializers.CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 如果是已登录用户，存储购物车到redis
            # 创建连接到redis的对象
            redis_conn = get_redis_connection('cart')

            # 管道
            pl = redis_conn.pipeline()

            # 修改hash里面的sku_id和count
            # 因为前后端约定购物车修改的数据传入的规则是幂等的，所以后端不需要判断sku_id是否存在，直接覆盖写入
            pl.hset('cart_%s' % user.id, sku_id, count)

            # 修改set里面的sku_id
            # 因为前后端约定购物车修改的数据传入的规则是幂等的，所以后端不需要判断sku_id是否存在，直接覆盖写入
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)

            # 记得执行
            pl.execute()

            # 响应
            return Response(serializer.data)
        else:
            # 如果是未登录用户，存储购物车到cookie
            # 读取出cookie中原有的购物车数据
            cookie_cart_str = request.COOKIES.get('cart')

            # 判断cookie中的购物车数据是否存在，如果存在再转字典；反之，给空字典
            if cookie_cart_str:
                cookie_cart_str_bytes = cookie_cart_str.encode()
                cookie_cart_dict_bytes = base64.b64decode(cookie_cart_str_bytes)
                cookie_cart_dict = pickle.loads(cookie_cart_dict_bytes)
            else:
                cookie_cart_dict = {}

            # 因为前后端约定购物车修改的数据传入的规则是幂等的，所以后端不需要判断sku_id是否存在，直接覆盖写入
            cookie_cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 生成新的购物车字符串
            new_cookie_cart_dict_bytes = pickle.dumps(cookie_cart_dict)
            new_cookie_cart_str_bytes = base64.b64encode(new_cookie_cart_dict_bytes)
            new_cookie_cart_str = new_cookie_cart_str_bytes.decode()

            # 构造响应对象
            response = Response(serializer.data)

            # 将新的字典转成新的购物车字符串，写入到cookie
            response.set_cookie('cart', new_cookie_cart_str)

            # 响应
            return response

    def delete(self, request):
        """删除购物车"""
        # 创建序列化器对象
        serializer = serializers.CartDeleteSerializer(data=request.data)
        # 校验参数
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')

        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 如果是已登录用户，存储购物车到redis
            # 创建连接到redis的对象
            redis_conn = get_redis_connection('cart')

            # 管道
            pl = redis_conn.pipeline()

            # 删除hash里面的sku_id和count对应的一条记录
            pl.hdel('cart_%s' % user.id, sku_id)

            # 删除set里面的sku_id
            pl.srem('selected_%s' % user.id, sku_id)

            # 记住执行
            pl.execute()

            # 响应
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # 如果是未登录用户，存储购物车到cookie
            # 读取出cookie中原有的购物车数据
            cookie_cart_str = request.COOKIES.get('cart')

            # 判断cookie中的购物车数据是否存在，如果存在再转字典；反之，给空字典
            if cookie_cart_str:
                cookie_cart_str_bytes = cookie_cart_str.encode()
                cookie_cart_dict_bytes = base64.b64decode(cookie_cart_str_bytes)
                cookie_cart_dict = pickle.loads(cookie_cart_dict_bytes)
            else:
                cookie_cart_dict = {}

            # 构造响应对象
            response = Response(status=status.HTTP_204_NO_CONTENT)

            # 删除指定的sku_id对应的记录
            if sku_id in cookie_cart_dict:
                del cookie_cart_dict[sku_id]

                # 生成新的购物车字符串
                new_cookie_cart_dict_bytes = pickle.dumps(cookie_cart_dict)
                new_cookie_cart_str_bytes = base64.b64encode(new_cookie_cart_dict_bytes)
                new_cookie_cart_str = new_cookie_cart_str_bytes.decode()

                # 将新的字典转成新的购物车字符串，写入到cookie
                response.set_cookie('cart', new_cookie_cart_str)

            # 响应
            return response

