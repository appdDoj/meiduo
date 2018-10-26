from urllib.parse import urlencode, parse_qs
from django.conf import settings
from urllib.request import urlopen
import json

from .exceptions import QQAPIException


import logging
# 日志记录器
logger = logging.getLogger('django')


class OAuthQQ(object):
    """QQ登录的工具类：封装了QQ登录的部分过程"""

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, state=None):
        """构造方法，用户初始化OAuthQQ对象，并传入一些参数"""
        self.client_id = client_id or settings.QQ_CLIENT_ID
        self.client_secret = client_secret or settings.QQ_CLIENT_SECRET
        self.redirect_uri = redirect_uri or settings.QQ_REDIRECT_URI
        self.state = state or settings.QQ_STATE

    def get_login_url(self):
        """提供QQ扫码登录页面的网址
        'https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=101474184&redirect_uri=xx
        &state=user_center_info.html&scope=get_user_info'
        """

        # 准备url
        login_url = 'https://graph.qq.com/oauth2.0/authorize?'

        # 准备参数
        params = {
            'response_type':'code',
            'client_id':self.client_id,
            'redirect_uri':self.redirect_uri,
            'state':self.state,
            'scope':'get_user_info'
        }

        # 将字典转成查询字符串格式
        query_params = urlencode(params)

        # url拼接参数
        # login_url = login_url + query_params
        login_url += query_params

        # 返回login_url
        return login_url

    def get_access_token(self, code):
        """
        使用code,获取access_token
        :param code: authorization code
        :return: access_token
        """
        # 准备url
        url = 'https://graph.qq.com/oauth2.0/token?'

        # 准备参数
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }

        # 将params字典转成查询字符串
        query_params = urlencode(params)

        # 拼接请求地址
        url += query_params

        try:
            # 美多商城向QQ服务器发送GET请求
            # (bytes)'access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14'
            response_data = urlopen(url).read()
            # (str)'access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14'
            response_str = response_data.decode()
            # 将response_str，转成字典
            response_dict = parse_qs(response_str)
            # 读取access_token
            access_token = response_dict.get('access_token')[0]
        except Exception as e:
            logger.error(e)
            # 在封装工具类的时候，需要捕获异常，并抛出异常，千万不要解决异常，谁用谁解决异常
            # BookInfo.objects.get()   类似于这样的一种思想
            raise QQAPIException('获取access_token失败')

        return access_token

    def get_open_id(self, access_token):
        """
        使用access_token获取openid
        :param access_token: 通过code 获取到的access_token
        :return: openid
        """
        # 准备请求地址
        url = 'https://graph.qq.com/oauth2.0/me?access_token=%s' % access_token

        response_str = ''
        try:
            # 美多商城向QQ服务器发送GET请求
            # (bytes)'callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} );'
            response_data = urlopen(url).read()
            response_str = response_data.decode()
            # callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} )\n;
            response_dict = json.loads(response_str[10:-4])
            # 读取openid
            open_id = response_dict.get('openid')
        except Exception as e:
            # 如果有异常，QQ服务器返回 "code=xxx&msg=xxx"
            err_data = parse_qs(response_str)
            logger.error(e)
            raise QQAPIException('code=%s msg=%s' % (err_data.get('code'), err_data.get('msg')))

        return open_id





















