#定义耗时的函数
# from utils.ytx_sdk.sendSMS import CCP
from celery_tasks.main import app

#为函数添加装饰器，这个函数就成为了celery的任务
@app.task
def send_sms_code(mobile,sms_code):
    try:
        # CCP.sendTemplateSMS(mobile,code,expires,template_id)
        print(sms_code)
    except:
        return '发送短信失败'