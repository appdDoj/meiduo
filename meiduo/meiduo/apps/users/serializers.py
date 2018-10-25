from rest_framework import serializers
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings
import re
from .models import User

#
# class UserCreateSerializer(serializers.Serializer):
#     # 定义属性
#     id=serializers.IntegerField(read_only=True)
#     #输出口令
#     token=serializers.CharField(read_only=True)
#     username = serializers.CharField(
#         min_length=5,
#         max_length=20,
#         error_messages={
#             'min_length': '用户名要求是5-20个字符',
#             'max_length': '用户名要求是5-20个字符',
#         }
#     )
#     password = serializers.CharField(
#         min_length=8,
#         max_length=20,
#         error_messages={
#             'min_length': '密码要求是8-20个字符',
#             'max_length': '密码要求是8-20个字符',
#         },
#         write_only=True
#     )
#     password2 = serializers.CharField(
#         min_length=8,
#         max_length=20,
#         error_messages={
#             'min_length': '确认密码要求是8-20个字符',
#             'max_length': '确认密码要求是8-20个字符',
#         },
#         #属性只接收客户端的数据，不向客户端响应
#         write_only=True
#     )
#     sms_code = serializers.IntegerField(write_only=True)
#     mobile = serializers.CharField()
#     allow = serializers.BooleanField(write_only=True)
#
#     # 验证validate_**
#     # 验证用户名是否存在
#     def validate_username(self, value):
#         count = User.objects.filter(username=value).count()
#         if count > 0:
#             raise serializers.ValidationError('用户名已经存在')
#         return value
#
#     # 验证手机号
#     def validate_mobile(self, value):
#         #正则匹配
#         if not re.match(r'^1[3-9]\d{9}$',value):
#             raise serializers.ValidationError('手机号格式错误')
#
#         #手机号是否重复
#         count = User.objects.filter(mobile=value).count()
#         if count > 0:
#             raise serializers.ValidationError('手机号已经存在')
#         return value
#
#     # 验证是否同意协议
#     def validate_allow(self, value):
#         if not value:
#             raise serializers.ValidationError('请先阅读并同意协议')
#         return value
#
#     def validate(self, attrs):
#         # attrs表示请求的所有数据，类型为字典
#
#         # 验证密码是否一致
#         password = attrs.get('password')
#         password2 = attrs.get('password2')
#         if password != password2:
#             raise serializers.ValidationError('两个密码不一致')
#
#         # 验证短信码
#         sms_code_request = attrs.get('sms_code')
#         mobile = attrs.get('mobile')
#         # 读取redis中的值
#         redis_cli = get_redis_connection('sms_code')
#         sms_code_redis = redis_cli.get('sms_code' + mobile)
#         # 判断是否有验证码
#         if not sms_code_redis:
#             raise serializers.ValidationError('短信验证码已经过期')
#         # 强制当前验证码过期
#         redis_cli.delete('sms_code' + mobile)
#         # 判断两个验证码是否相等
#         if int(sms_code_redis) != int(sms_code_request):
#             raise serializers.ValidationError('短信验证码错误')
#
#         return attrs
#
#     # 创建create
#     def create(self, validated_data):
#         # user=User.objects.create(**validated_data)
#         user = User()
#         user.username = validated_data.get('username')
#         user.set_password(validated_data.get('password'))
#         user.mobile = validated_data.get('mobile')
#         user.save()
#
#         #当用户注册成功后，认为登录，则需要进行状态保持===>获取token
#         jwt_payload_handler=api_settings.JWT_PAYLOAD_HANDLER
#         jwt_encode_handler=api_settings.JWT_ENCODE_HANDLER
#         payload=jwt_payload_handler(user)
#         token=jwt_encode_handler(payload)
#         user.token=token
#
#         return user


class UserCreateSerializer(serializers.ModelSerializer):
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
        redis_conn = get_redis_connection('verify_codes')
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
