from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^cart/$', views.CartView.as_view()),  # 购物车
    url(r'^cart/selection/$', views.CartSelectAllView.as_view()),  # 购物车全选
]