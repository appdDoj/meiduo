from django.shortcuts import render
from rest_framework.views import APIView

# Create your views here.

# url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
class QQAuthURLView(APIView):
    """提供QQ登录页面网址"""
    def get(self, request):
        pass
