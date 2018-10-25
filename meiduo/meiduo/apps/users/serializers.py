from rest_framework import serializers
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings
import re
from .models import User


class UserCreateSerializer(serializers.Serializer):
    # 定义属性
    id=serializers.IntegerField(read_only=True)
    #输出口令
    token=serializers.CharField(read_only=True)
    username = serializers.CharField(
        min_length=5,
        max_length=20,
        error_messages={
            'min_length': '用户名要求是5-20个字符',
            'max_length': '用户名要求是5-20个字符',
        }
    )
    password = serializers.CharField(
        min_length=8,
        max_length=20,
        error_messages={
            'min_length': '密码要求是8-20个字符',
            'max_length': '密码要求是8-20个字符',
        },
        write_only=True
    )
    password2 = serializers.CharField(
        min_length=8,
        max_length=20,
        error_messages={
            'min_length': '确认密码要求是8-20个字符',
            'max_length': '确认密码要求是8-20个字符',
        },
        #属性只接收客户端的数据，不向客户端响应
        write_only=True
    )
    sms_code = serializers.IntegerField(write_only=True)
    mobile = serializers.CharField()
    allow = serializers.BooleanField(write_only=True)

    # 验证validate_**
    # 验证用户名是否存在
    def validate_username(self, value):
        count = User.objects.filter(username=value).count()
        if count > 0:
            raise serializers.ValidationError('用户名已经存在')
        return value

    # 验证手机号
    def validate_mobile(self, value):
        #正则匹配
        if not re.match(r'^1[3-9]\d{9}$',value):
            raise serializers.ValidationError('手机号格式错误')

        #手机号是否重复
        count = User.objects.filter(mobile=value).count()
        if count > 0:
            raise serializers.ValidationError('手机号已经存在')
        return value

    # 验证是否同意协议
    def validate_allow(self, value):
        if not value:
            raise serializers.ValidationError('请先阅读并同意协议')
        return value

    def validate(self, attrs):
        # attrs表示请求的所有数据，类型为字典

        # 验证密码是否一致
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError('两个密码不一致')

        # 验证短信码
        sms_code_request = attrs.get('sms_code')
        mobile = attrs.get('mobile')
        # 读取redis中的值
        redis_cli = get_redis_connection('sms_code')
        sms_code_redis = redis_cli.get('sms_code' + mobile)
        # 判断是否有验证码
        if not sms_code_redis:
            raise serializers.ValidationError('短信验证码已经过期')
        # 强制当前验证码过期
        redis_cli.delete('sms_code' + mobile)
        # 判断两个验证码是否相等
        if int(sms_code_redis) != int(sms_code_request):
            raise serializers.ValidationError('短信验证码错误')

        return attrs

    # 创建create
    def create(self, validated_data):
        # user=User.objects.create(**validated_data)
        user = User()
        user.username = validated_data.get('username')
        user.set_password(validated_data.get('password'))
        user.mobile = validated_data.get('mobile')
        user.save()

        #当用户注册成功后，认为登录，则需要进行状态保持===>获取token
        jwt_payload_handler=api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler=api_settings.JWT_ENCODE_HANDLER
        payload=jwt_payload_handler(user)
        token=jwt_encode_handler(payload)
        user.token=token

        return user

