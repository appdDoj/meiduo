from rest_framework import serializers
import re
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings
from celery_tasks.email.tasks import send_verify_email
from .models import User, Address
from goods.models import SKU
# from meiduo.apps.goods.models import SKU


class UserBrowseHistorySerializer(serializers.Serializer):
    """用户浏览记录序列化器
    做校验和序列化话
    """
    sku_id = serializers.IntegerField(label='商品SKU ID', min_value=1)

    # 单独校验sku_id
    def validate_sku_id(self, value):
        """
        校验sku_id
        :param value: sku_id
        :return: value
        """
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('无效的sku_id')

        return value

    def create(self, validated_data):
        """重写序列化器的保存的方法
        目的：自己将sku_id存储到redis数据库
        """
        # 读取登录用户的id
        user_id = self.context['request'].user.id
        # 读取商品sku_id
        sku_id = validated_data.get('sku_id')

        # 创建连接到redis的对象
        redis_conn = get_redis_connection('history')
        # 管道
        pl = redis_conn.pipeline()

        # 去重
        # redis_conn.lrem('history_%s' % user_id, 0, sku_id)
        pl.lrem('history_%s' % user_id, 0, sku_id)

        # 保存
        # redis_conn.lpush('history_%s' % user_id, sku_id)
        pl.lpush('history_%s' % user_id, sku_id)

        # 截取
        # redis_conn.ltrim('history_%s' % user_id, 0, 4)
        pl.ltrim('history_%s' % user_id, 0, 4)

        # 执行
        pl.execute()

        # 去重
        redis_conn.lrem('history_%s' % user_id, 0, sku_id)

        # 保存
        redis_conn.lpush('history_%s' % user_id, sku_id)

        # 截取
        redis_conn.ltrim('history_%s' % user_id, 0, 4)

        # 响应sku_id
        return validated_data



class UserAddressSerializer(serializers.ModelSerializer):
    """
    用户地址序列化器
    """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def validate_mobile(self, value):
        """
        验证手机号
        """
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def create(self, validated_data):
        """
        保存
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址标题
    """
    class Meta:
        model = Address
        fields = ('title',)




class EmailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'email']
        extra_kwargs = {
            # 因为email在定义模型字段时可以为空,所以序列化器在映射该字段时默认是非必传的
            # 由于这里就是跟新email,所以重新指定为必传的
            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        """
        重写序列化器的更新数据的方法
        1.用于有目的的更新某些字段,（提示：put方法时全字段更新，重写可以实现指定字段的更新）
        2.用于在此处发送邮件
        :param instance: 外界传入的user模型对象
        :param validated_data: 经过验证的数据
        :return: instance
        """
        instance.email = validated_data.get('email')
        instance.save()
        # 生成激活连接
        verify_url = instance.generate_verify_email_url()

        # 触发发送邮件的异步任务
        # 注意点：必须调用delayY用于触发异步任务
        send_verify_email.delay(instance.email, verify_url)

        return instance


class UserDetailSerializer(serializers.ModelSerializer):
    """用户基本信息序列化器: 做序列化"""

    class Meta:
        model = User
        fields = ['id', 'username', 'mobile', 'email', 'email_active']

class CreateUserSerializer(serializers.ModelSerializer):
    """注册的校验序列化器"""

    # 定义模型类属性以外的字段
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    token = serializers.CharField(label='登录状态token', read_only=True)

    class Meta:
        model = User
        # ['id', 'username', 'mobile'] ：输出，序列化（id默认是read_only,username和mobile是双向的）
        # ['password', 'password2', 'sms_code', 'allow'] ：输入，反序列化
        fields = ['id', 'username', 'mobile', 'password', 'password2', 'sms_code', 'allow', 'token']
        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    # 追加字段的校验逻辑
    def validate_mobile(self, value):
        """验证手机号"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def validate_allow(self, value):
        """检验用户是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, data):
        # 判断两次密码
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 判断短信验证码
        redis_conn = get_redis_connection('sms_code')
        mobile = data['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data

    def create(self, validated_data):
        """
        创建用户
        需要重写父类的create方法，因为作为write_only的三个字段【password2，sms_code，allow】，在模型类中不需要存储，移除掉
        """
        # 移除数据库模型类中不存在的属性
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        # 调用CreateModelMixin的创建模型对象的方法
        user = super().create(validated_data)

        # 调用django的认证系统加密密码
        user.set_password(validated_data['password'])
        user.save()

        # 保存注册数据之后，响应注册结果之前
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        # 当前的注册用户对象
        payload = jwt_payload_handler(user)
        # JWT token
        token = jwt_encode_handler(payload)

        # 将token临时绑定到user,一并响应出去
        user.token = token

        return user
