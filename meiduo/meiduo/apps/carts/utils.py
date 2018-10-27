import base64
import pickle
from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """合并cookie购物车到redis购物车"""

    # 读取cookie中的购物车数据
    cookie_cart_str = request.COOKIES.get('cart')

    # 判断cookie中的购物车数据是否存在，如果存在再转字典；反之，直接返回
    if not cookie_cart_str:
        return response

    # 将购物车数据转字典
    cookie_cart_str_bytes = cookie_cart_str.encode()
    cookie_cart_dict_bytes = base64.b64decode(cookie_cart_str_bytes)
    cookie_cart_dict = pickle.loads(cookie_cart_dict_bytes)
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

    # 读取redis中的购物车数据
    redis_conn = get_redis_connection('cart')
    # 读取hash中的sku_id和count
    # {
    #     b'sku_id_1':b'count_1',
    #     b'sku_id_2':b'count_2',
    # }
    redis_cart_dict = redis_conn.hgetall('cart_%s' % user.id)

    # 读取set中的sku_id
    # [b'sku_id_1']
    redis_cart_selected = redis_conn.smembers('selected_%s' % user.id)

    # 准备一个新的中间字典:为了收集redis中原有的数据。也为了保证在合并的时候，redis购物车类型和cookie购物车类型一样
    # {
    #     sku_id_1:count_1,
    #     sku_id_2':count_2,
    # }
    new_redis_cart_dict = {}
    for sku_id, count in redis_cart_dict.items():
        new_redis_cart_dict[int(sku_id)] = int(count)

    # 遍历cookie中的购物车数据，合并到redis购物车
    for sku_id, cookie_cart in cookie_cart_dict.items():
        new_redis_cart_dict[sku_id] = cookie_cart['count']

        if cookie_cart['selected']:
            # redis_cart_selected : 集合对象，add()方法是直接向集合中最佳元素。类似于列表的insert()方法
            redis_cart_selected.add(sku_id)

    # 将new_redis_cart_dict和redis_cart_selected里面的购物车数据同步到redis
    pl = redis_conn.pipeline()
    pl.hmset('cart_%s' % user.id, new_redis_cart_dict)
    pl.sadd('selected_%s' % user.id, *redis_cart_selected)
    pl.execute()

    # 清空cookie中的购物车
    response.delete_cookie('cart')

    # 一定要将response返回到视图中，在视图中才能将response对象交给用户
    return response