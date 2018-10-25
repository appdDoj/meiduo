from django.contrib.auth.backends import ModelBackend
import re

from .models import User


def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义jwt认证成功返回数据
    """
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }


def get_user_by_account(account):
    """
    根据account查询用户
    :param account: 可以是用户名，也可以是手机号
    :return: user 、 None
    """
    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """自定义用户认证的方式"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写用户认证的方法
        :param request: 本次登录请求对象
        :param username: 本次登录请求用户名
        :param password: 本次登录请求密码（明文）
        :param kwargs: 其他的参数
        :return: 如果该用户是本网站的用户，返回user对象；反之，返回None
        """
        # 查询user对象
        user = get_user_by_account(username)

        # 校验user是否存在和密码是否正确
        if user and user.check_password(password):
            return user
