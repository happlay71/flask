import os
from flask.cli import with_appcontext


COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()


import sys  # 代码覆盖度检测
import click
from app import create_app, db
from app.models import User, Follow, Role, Permission, Post, Comment
from flask_migrate import Migrate, upgrade  # 迁移数据库 deploy命令


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)  # 初始化Flask-Migrate
# app.cli.profile()

# 添加一个shell上下文，不用都每次导入数据
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Follow=Follow, Role=Role,
                Permission=Permission, Post=Post, Comment=Comment)

# 覆盖度检测
@app.cli.command()  # 用于将下面的函数注册为Flask应用的命令行命令
@click.option('--coverage/--no-coverage', default=False,
              help='Run tests under code coverage.')  # 用于定义命令行选项
@click.argument('test_names', nargs=-1)
def test(coverage, test_names):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import subprocess  # 运行脚本时启用代码覆盖率
        os.environ['FLASK_COVERAGE'] = '1'
        sys.exit(subprocess.call(sys.argv))

    import unittest  # 用于运行测试
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover('tests')  # 自动发现位于tests目录下的所有测试
    unittest.TextTestRunner(verbosity=2).run(tests)  # 创建实例，输出详细测试结果，运行tests项目
    if COV:
        COV.stop()
        COV.save()  # 保存代码覆盖的数据
        print('Coverage Summary:')
        COV.report()  # 打印代码覆盖的汇总报告
        basedir = os.path.abspath(os.path.dirname(__file__))  # 存储的是当前脚本文件所在的绝对路径
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)  # 生成HTML格式的代码覆盖报告
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()  # 清除代码覆盖的数据
    
# 在请求分析器的监视下运行应用
@app.cli.command()
@click.option('--length', default=25,
              help='Number of functions to include in the profiler report.')
@click.option('--profile-dir', default=None,
              help='Directory where profiler data files are saved.')
@with_appcontext
def profile(length, profile_dir):
    """Start the application under the code profiler."""
    from werkzeug.middleware.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length], profile_dir=profile_dir)
    # with app.test_request_context('/profile'):
    #     print(request.path)
    app.run(debug=False)

# 自动程序--deploy命令
@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # 把数据库迁移到最新修订版本
    upgrade()

    # 创建或更新用户角色
    Role.insert_roles()

    # 确保所有用户都关注了他们自己
    User.add_self_follows()
    

# if __name__ == '__main__':
#     app.run()



