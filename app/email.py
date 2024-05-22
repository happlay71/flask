from flask import render_template, current_app
from flask_mail import Message  # 电子邮件
from threading import Thread  # 异步发送电子邮件
from . import mail

# 异步发送电子邮件
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

# send_email函数接受收件人地址to、邮件主题subject、邮件模板template以及其他关键字参数kwargs作为输入
def send_email(to, subject, template, **kwargs):
    # 创建一个Message对象，其中设置了邮件的发送者、收件人和邮件主题
    # ['FLASKY_MAIL_SUBJECT_PREFIX']用于添加邮件主题的前缀
    # ['FLASKY_MAIL_SENDER']用于设置邮件的发件人信息
    app = current_app._get_current_object()
    msg = Message(current_app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=current_app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    # 将模板文件渲染为纯文本和HTML格式的邮件内容
    msg.body = render_template(template + '.txt', **kwargs)  # 名为template, 纯文本，**kwargs是传递给模板的关键字参数，用于替换模板中的变量
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])  # 异步发送电子邮件
    thr.start()
    return thr



