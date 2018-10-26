from urllib.parse import urlencode
from django.conf import settings


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

    def get_access_token(self):
        """"""
        pass





