from flask import Flask, render_template, Blueprint
from flask_bootstrap import Bootstrap  # 创建整洁的网页界面
from flask_mail import Mail  # 电子邮件
from flask_moment import Moment  # 设置时间
from flask_sqlalchemy import SQLAlchemy  # 配置数据库
from config import config
from flask_login import LoginManager  # 初始化Flask-Login
from flask_pagedown import PageDown  # 富文本



bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # 设置登录视图，即未登录用户访问受保护的路由时会被重定向到该视图
pagedown = PageDown()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 初始化功能
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)


    # 添加路由和自定义的错误页面，注册蓝本
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    

    return app



