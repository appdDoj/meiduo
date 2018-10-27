from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from alipay import AliPay
from django.conf import settings
import os
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from orders.models import OrderInfo
from .models import Payment
# Create your views here.


# payment/status/
class PaymentStatusView(APIView):
    """保存支付结果"""

    def put(self, request):
        """获取支付宝重定向过程中传递的trade_no和out_trade_no并保存
        trade_no ： 是支付宝维护的订单流水号
        out_trade_no ： 是美多维护的订单id
        """
        # 读取所有的查询字符串
        # Django里面的查询字符串时Query_Dict类型的数据（提供一键一值，一键多值，get(), getlist()）
        query_dict = request.query_params
        # 将query_dict转成标准的字典：为了方便后续的读取和移除"sign"
        data = query_dict.dict()

        # 从查询字符串中读取"sign":先把"sign"从data字典中移除掉，顺便接受一下
        # 1.从data中移除"sign"是为了方便后续对data使用RSA2签名计算，再跟signature对比
        # 2.对比的目的：为了识别当前的回调是否是支付宝的回调
        signature = data.pop("sign")

        # 创建对接alipay的对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,  # 创建的应用的id
            app_notify_url=None,  # 默认回调url,本案例选择returnUrl，所以传入None
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2(默认推荐的)
            debug=settings.ALIPAY_DEBUG  # 默认False，如果是测试环境，传入True
        )

        # 使用没有是"sign"的data，去使用RSA2签名计算，再跟signature对比
        success = alipay.verify(data, signature)
        if success:
            # 读取out_trade_no和trade_no
            out_trade_no = data.get('out_trade_no')
            trade_no = data.get('trade_no')

            # 表示本次回调确实来自于支付宝：保存支付的结果和更改订单的状态
            Payment.objects.create(
                order_id=out_trade_no,
                trade_id = trade_no
            )

            # 跟新订单状态
            OrderInfo.objects.filter(order_id=out_trade_no, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(status=OrderInfo.ORDER_STATUS_ENUM["UNSEND"])

            # 返回保存的结果
            return Response({'trade_id':trade_no})
        else:
            return Response({'message': '非法请求'}, status=status.HTTP_403_FORBIDDEN)


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
