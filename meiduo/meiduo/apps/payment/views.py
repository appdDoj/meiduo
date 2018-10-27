from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from alipay import AliPay
from django.conf import settings
import os
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from orders.models import OrderInfo
# Create your views here.


# orders/(?P<order_id>\d+)/payment/
class PaymentView(APIView):
    """对接支付宝的支付"""

    # 指定登录权限
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """向支付宝索取登录支付连接并响应给用户"""

        # 读取登录用户user
        user = request.user

        # 查询当前要支付的订单
        # 要支付的订单必须是当前登录用户下的订单，并且订单的状态是待支付的状态
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return Response({'message':'订单不存在'}, status=status.HTTP_400_BAD_REQUEST)

        # 创建对接alipay的对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID, # 创建的应用的id
            app_notify_url=None,  # 默认回调url,本案例选择returnUrl，所以传入None
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2(默认推荐的)
            debug=settings.ALIPAY_DEBUG  # 默认False，如果是测试环境，传入True
        )

        # 访问alipay的支付接口
        # 正式的：电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        # 测试的：电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id, # 美多自己维护的订单id
            total_amount=str(order.total_amount), # 要支付的总金额
            subject="美多商城%s" % order_id, # 支付标题
            return_url="http://www.meiduo.site:8080/pay_success.html", # 订单支付成功之后的回调页面
        )

        # 拼接支付宝登录支付连接
        alipay_url = settings.ALIPAY_URL + '?' + order_string

        return Response({'alipay_url':alipay_url})
