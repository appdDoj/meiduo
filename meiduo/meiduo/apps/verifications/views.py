from django.http import HttpResponse
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
import random


# from utils.ytx_sdk.sendSMS import CCP

from . import serializers


# url(r'^image_codes/(?P<mobile>1[3-9]\d{9})/$', views.ImageCodeView.as_view()),
from meiduo.libs.captcha.captcha import captcha
import logging
from . import constants


# url('^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),
class SMSCodeView(GenericAPIView):
    """发送短信"""

    # 指定序列化器
    serializer_class = serializers.ImageCodeCheckSerializer

    def get(self, request, mobile):
        # 接受参数：mobile,image_code_id,text
        # 校验参数：image_code_id, text
        # 对比text和服务器存储的图片验证码内容

        # 创建序列化器对象
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 生成随机短信验证码:不够6位需要补0
        sms_code = '%06d' % random.randint(0, 999999)

        # 发送短信验证码
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)

        # 存储短信验证码
        redis_conn = get_redis_connection('verify_codes')
        # redis_conn.setex('key', 'time', 'value')

        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_EXPIRES, sms_code)
        #
        # # 存储是否60s重复发送短信的标记
        # redis_conn.setex('send_flag_%s' % mobile, constants.SMS_FLAG_EXPIRES, 1)

        # 使用管道，让redis的多个指令只需要访问一次redis数据库，就可以一次性执行完多个指令
        pl = redis_conn.pipeline()

        # 存储短信验证码
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_EXPIRES, sms_code)
        # 存储是否60s重复发送短信的标记
        pl.setex('send_flag_%s' % mobile, constants.SMS_FLAG_EXPIRES, 1)

        # 注意：记得一定要调用execute()
        pl.execute()
        # 响应发送短信验证码结果
        return Response({'message':'OK'})


# url(r'^image_codes/(?P<image_code_id>[\w-]+)/$', views.ImageCodeView.as_view()),
class ImageCodeView(APIView):
    """图片验证码"""

    def get(self, request, image_code_id):
        """提供图片验证码"""

        # 生成图片验证码的内容和图片
        text, image = captcha.generate_captcha()


        # 将图片验证码的内容存储到redis
        redis_conn = get_redis_connection('verify_codes')
        redis_conn.set('img_%s' % image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)

        # 将图片响应给用户
        return HttpResponse(image, content_type='image/jpg')