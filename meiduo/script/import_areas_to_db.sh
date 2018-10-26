#!/bin/bash
mysql -h数据库ip地址 -u数据库用户名 -p 数据库密码 < areas.sql
例如：
mysql -h192.168.103.132 -uroot -pmysql meiduo_mall_04 < areas.sql
mysql -h127.0.0.1 -uroot -proot meiduo18 < areas.sql
        'NAME': 'meiduo18',
        'HOST': 'localhost',
        'PORT': 3306,
        'USER': 'meiduo_sz18',
        'PASSWORD': 'meiduo',
mysql  -uroot -p meiduo18  < areas.sql
导出数据库指定的表
mysqldump -uroot -p meiduo18 tb_areas  > tb_areas.sql