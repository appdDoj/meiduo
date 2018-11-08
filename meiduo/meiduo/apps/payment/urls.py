from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^orders/(?P<order_id>\d+)/payment/$', views.PaymentView.as_view()),  # 获取支付链接
    url(r'^payment/status/$', views.PaymentStatusView.as_view()),  # 支付结果设置
]