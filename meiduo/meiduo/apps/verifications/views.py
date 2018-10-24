from django.shortcuts import render
from rest_framework.views import APIView

# Create your views here.


# url(r'^image_codes/(?P<mobile>1[3-9]\d{9})/$', views.ImageCodeView.as_view()),
class SMSCodeView(APIView):
    """图片验证码"""

    def get(self, request, image_code_id):
        """提供图片验证码"""
        pass