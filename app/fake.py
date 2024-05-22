# 创建虚拟博客文章数据
from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db
from .models import User, Post


def  users(count=100):
    fake = Faker()  # 用于生成虚拟数据
    i = 0
    while i < count:
        u = User(email=fake.email(),
                 username=fake.user_name(),
                 password='password',
                 confirmed=True,
                 name=fake.name(),
                 location=fake.city(),
                 about_me=fake.text(),
                 member_since=fake.past_date())
        db.session.add(u)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()


def posts(count=100):
    fake = Faker()
    user_count = User.query.count()  # 获取数据库中用户表的记录总数，用于随机选择帖子的作者
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()  # 通过偏移量来随机选择数据库中的一条用户记录
        p = Post(body=fake.text(),
                 timestamp=fake.past_date(),
                 author=u)
        db.session.add(p)
    db.session.commit()





