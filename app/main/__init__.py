import os
from flask import Blueprint  # 设置蓝图
from ..models import Permission

main = Blueprint('main', __name__, static_folder=os.path.join(os.path.abspath(os.path.dirname(__file__))
                                                              , '..', 'static'))

# 注册Permission全局变量到模板中，不用每次都传入该类的实例
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

from . import views, errors, forms

