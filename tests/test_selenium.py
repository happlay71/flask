import threading
import unittest
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from app import create_app, db, fake
from app.models import User, Role


# driver_path = 'E:/E/GoogleDriver/Windows/chromedriver.exe' 
# service = Service(executable_path=driver_path)


class SeleniumTestCase(unittest.TestCase):
    client = None
    

    @classmethod
    def setUpClass(cls):
        # 启动Chrome
        options = webdriver.ChromeOptions()
        options.add_argument('headless')  # 在无界面的Chrome实例中运行，可注释
        try:
            cls.client = webdriver.Chrome(options=options)
        except:
            pass

        # 如果无法启动浏览器，跳过这些测试
        if cls.client:
            # 创建应用
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()
            
            #禁止日志，保持输出整洁
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            # 创建数据库，并使用一些虚拟数据填充
            db.create_all()
            Role.insert_roles()
            fake.users(10)
            fake.posts(10)

            # 添加管理员
            admin_role = Role.query.filter_by(name='Administrator').first()
            admin = User(email='john@example.com',
                         username='john', password='cat',
                         role=admin_role, confirmed=True)
            db.session.add(admin)
            db.session.commit()

            # 在一个线程中启动Flask服务器
            cls.server_thread = threading.Thread(
                target=cls.app.run, kwargs={'debug': 'false',
                                            'use_reloader': False,
                                            'use_debugger': False})
            cls.server_thread.start()


    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # 关闭Flask服务器和浏览器
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            cls.server_thread.join()

            # 销毁数据库
            db.drop_all()
            db.session.remove()

            # 删除应用上下文
            cls.app_context.pop()


    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')
        

    def tearDown(self):
        pass


    def test_admin_home_page(self):
        # 进入首页
        self.client.get('http://localhost:5000/')
        self.assertIn(r'<h1>Hello,Stranger!</h1>', self.client.page_source)
        
        # 进入登陆页面
        self.client.find_element(By.LINK_TEXT, 'Log In').click()
        self.assertIn('<h1>Login</h1>', self.client.page_source)

        # 登录
        self.client.find_element(By.NAME, 'email').\
            send_keys('john@example.com')
        self.client.find_element(By.NAME, 'password').send_keys('cat')
        self.client.find_element(By.ID, 'submit').click()

        # 等待一段时间，确保页面跳转完成（根据需要进行调整）
        self.client.implicitly_wait(5)  # 等待5秒
        # 跳转到首页
        self.client.get('http://localhost:5000/user/john')

        self.assertIn(r'<h1>Hello,john!</h1>', self.client.page_source)

        # 进入用户资料页面
        # self.client.find_element(By.XPATH, "//input[@value='Profile']").click()
        # self.assertIn('<h1>john</h1>', self.client.page_source)
