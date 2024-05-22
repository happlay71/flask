#!/bin/sh
source venv/bin/activate
flask deploy
exec gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - flasky:app


# #!/bin/sh

# # 激活 Conda 环境（如果需要）
# . /opt/conda/etc/profile.d/conda.sh
# conda activate nenv

# # 如果你的 Flask 应用需要在部署时执行一些操作，可以在这里添加
# flask deploy
# # 启动 Gunicorn 服务器，将 Flask 应用运行在 0.0.0.0:5000
# exec gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - flasky:app


