import unittest
from flask import current_app
from app import create_app, db


class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')  # 创建了一个测试用的Flask应用，使用了测试配置（testing配置）
        self.app_context = self.app.app_context()  # 创建了一个应用上下文
        self.app_context.push()  # 激活应用上下文，这样在测试中可以使用 current_app 来获取当前的Flask应用实例
        db.create_all()  # 创建数据库中的所有表格

    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()  # 移除应用上下文

    
    def test_app_exists(self):
        self.assertFalse(current_app is None)


    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])




