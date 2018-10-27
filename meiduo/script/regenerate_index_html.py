#!/usr/bin/env python

"""
功能：手动生成所有SKU的静态index html文件
使用方法:
    ./regenerate_index_html.py
"""
import sys
# .../meiduo/meiduo

sys.path.insert(0, '../')
print(sys.path)

import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo.settings.dev'

 # 让django进行初始化设置
import django
django.setup()


from meiduo.apps.contents.crons import generate_static_index_html
# from contents.crons import generate_static_index_html


if __name__ == '__main__':
    generate_static_index_html()