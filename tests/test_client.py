# 使用flask测试客户端编写的测试框架
import re
import unittest
from app import create_app, db
from app.models import User, Role


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)  # 创建测试客户端，在发送请求时使用 cookies


    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Stranger' in response.get_data(as_text=True))  # as_text将字节数组转换为字符串


    def test_register_and_login(self):
        # 注册新账户
        response = self.client.post('/auth/register', data={
            'email': 'john@example.com',
            'username': 'john',
            'password': 'cat',
            'password2': 'cat'
        })
        # 用于获取HTTP响应的状态码
        self.assertEqual(response.status_code, 302)  # 注册成功表示为重定向

        # 使用新注册的账户登录
        response = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat'
        }, follow_redirects=True)  # post请求后跟随重定向
        self.assertEqual(response.status_code, 200)
        # get_data(as_text=True)获取页面并进行文本处理，可进行正则搜索
        self.assertTrue(re.search('Hello,\s+john!',
                                  response.get_data(as_text=True)))  # 首先匹配 "Hello,"，然后至少匹配一个或多个空格 \s+，最后匹配 "john"
        self.assertTrue(
            'You have not confirmed your account yet' in response.get_data(
            as_text=True))
        
        # 发送确认令牌
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get('/auth/confirm/{}'.format(token),
                                   follow_redirects=True)
        user.confirm(token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            'You have confirmed your account' in response.get_data(
            as_text=True))
        
        # 退出
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('You have been logged out' in response.get_data(
            as_text=True))
    


