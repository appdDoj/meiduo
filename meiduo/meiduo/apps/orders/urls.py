from django.conf.urls import url

from . import views


urlpatterns = [
    # 确认订单
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view()),
]