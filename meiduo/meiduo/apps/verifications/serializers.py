from rest_framework import serializers
from django_redis import get_redis_connection
from redis import RedisError

import logging
# 日志记录器
logger = logging.getLogger('django')


class ImageCodeCheckSerializer(serializers.Serializer):
    """校验图片验证码的序列化器"""

    # 定义校验字段:定义的校验字段要么和模型类的属性一样，要么和参数的key一样
    image_code_id = serializers.UUIDField()
    text = serializers.CharField(min_length=4, max_length=4)

    def validate(self, attrs):
        """
        对text和image_code_id联合校验
        :param attrs: validated_data
        :return: 如果校验成功，返回，attrs；反之，抛出异常
        """
        # 读取validated_data里面的数据
        image_code_id = attrs.get('image_code_id')
        text = attrs.get('text')

        # 获取连接到redis的对象
        redis_conn = get_redis_connection('verify_codes')

        # 获取redis中存储的图片验证码
        image_code_server = redis_conn.get('img_%s' % image_code_id)
        if image_code_server is None:
            raise serializers.ValidationError('无效验证码')

        # 删除图片验证码，防止暴力测试：必须先拿到再删除
        # 删除图片验证码是附带的可有可无的业务逻辑，不能让他阻塞主线的业务逻辑，所以出现了异常，不需要响应数据，忽略异常后，后续逻辑继续执行
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except RedisError as e:
            logger.error(e)

        # 需要先将bytes类型的image_code_server，转成字符串
        # py3的redis存储的数据，读取出来以后都是bytes类型的
        image_code_server = image_code_server.decode()

        # 对比text和服务器存储的图片验证码
        if text.lower() != image_code_server.lower():
            raise serializers.ValidationError('图片验证码输入有误')

        # 判断用户是否在60s内使用同一个手机号码获取短信
        mobile = self.context['view'].kwargs['mobile']
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            raise serializers.ValidationError('频繁发送短信')

        return attrs
