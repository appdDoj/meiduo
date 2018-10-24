from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
import random


# from utils.ytx_sdk.sendSMS import CCP

from rest_framework import serializers


# url(r'^image_codes/(?P<mobile>1[3-9]\d{9})/$', views.ImageCodeView.as_view()),
from . import constants


class SMSCodeView(APIView):
    """图片验证码"""

    def get(self, request, mobile):
        """提供图片验证码"""
        # 创建redis连接，相关的配置在dev.py中的cache
        redis_cli = get_redis_connection('sms_code')
        # 将验证码、标记存入redis
        # 如果标记存在则说明已经发过，不再发，如果标记不存在则发短信

        # 判断：是否向此手机号发过短信
        if redis_cli.get('sms_flag' + mobile):
            raise serializers.ValidationError('请60秒后再发短信')

        # 生成随机的6位数，作为验证码
        code = random.randint(100000, 999999)

        # 创建redis管道，只交互一次
        redis_pipeline = redis_cli.pipeline()
        # 保存验证码
        redis_pipeline.setex('sms_code' + mobile, constants.SMS_CODE_EXPIRES, code)
        # 保存发送标记
        redis_pipeline.setex('sms_flag' + mobile, constants.SMS_FLAG_EXPIRES, 1)
        # 执行
        redis_pipeline.execute()

        # 发短信
        # CCP.sendTemplateSMS(mobile,code,constants.SMS_CODE_EXPIRES/60,1)
        # print(code)
        # 调用celery的任务：任务名.delay(参数)
        send_sms_code.delay(mobile, code, constants.SMS_CODE_EXPIRES / 60, 1)

        # 响应
        return Response({'message': 'OK'})
