"""meiduo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import xadmin
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    # url(r'^admin/', admin.site.urls),

    # xadmin的路由
    url(r'xadmin/', include(xadmin.site.urls)),
    # users
    url('^', include('users.urls')),
    # 验证模块
    url('^', include('verifications.urls')),
    # verifications
    url(r'^', include('verifications.urls')),
   # oauth
    url(r'^oauth/', include('oauth.urls')),
   # areas
    url(r'^', include('areas.urls')),
    # 富文本编辑器
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    # goods
    url(r'^', include('goods.urls')),
    # carts
    url(r'^', include('carts.urls')),
    # orders
    url(r'^', include('orders.urls')),
    # payment
    url(r'^', include('payment.urls')),
]
