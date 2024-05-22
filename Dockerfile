# 使用 Python 3.10.6 版本的 Alpine 基础镜像
FROM python:3.10.6-alpine

# 设置 Flask 环境变量
ENV FLASK_APP flasky.py
ENV FLASK_CONFIG docker

# 添加一个名为 flasky 的用户, -D禁止提示用户输入密码
RUN adduser -D flasky  

# 切换用户为 flasky
USER flasky

# 设置工作目录
WORKDIR /home/flasky

# 复制项目中的 environment 文件夹到镜像中
COPY environment requirements

# # 使用 conda 创建环境并安装依赖
# RUN /home/flasky/miniconda/bin/conda env create -f environment.yml

# 激活 conda 环境
# RUN /home/flasky/miniconda/bin/conda activate nenv

RUN python -m venv venv
RUN venv/bin/pip install -r requirements/docker.txt

# # 使用 conda 创建环境并安装依赖
# RUN conda env create -f environment.yml

# # 激活 conda 环境
# SHELL ["conda", "run", "-n", "nenv", "/bin/bash", "-c"]


# 复制项目文件到镜像中
COPY app app
COPY migrations migrations
COPY flasky.py config.py boot.sh ./

# # 安装其他依赖包
# RUN /home/flasky/miniconda/envs/nenv/bin/pip install -r requirements/docker.txt

# 运行时配置
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]

# -------------------------------------------------------------------------- #

# # 使用 Miniconda3 作为基础镜像
# FROM continuumio/miniconda3:latest

# # 设置 Flask 环境变量
# ENV FLASK_APP flasky.py
# ENV FLASK_CONFIG docker

# # 添加一个名为 flasky 的用户, -D禁止提示用户输入密码
# RUN useradd -m flasky

# # 切换用户为 flasky
# USER flasky

# # 设置工作目录
# WORKDIR /home/flasky


# COPY environment requirements
# # COPY environment/environment_ubuntu.yml requirements/

# # # 切换到root用户
# # USER root

# # 创建 Conda 环境并安装依赖
# # RUN pip cache purge
# # 更新 conda
# # RUN conda update -n base -c defaults conda
# RUN conda env create -f requirements/docker_ubuntu.yml

# # # 切换回普通用户（可选，根据需要决定）
# # USER flasky

# # 复制项目文件到镜像中
# COPY app app
# COPY migrations migrations
# COPY flasky.py config.py boot.sh ./

# # 暴露容器端口
# EXPOSE 5000

# # 运行 Flask 应用
# ENTRYPOINT ["./boot.sh"]

# # # 激活 Conda 环境
# # SHELL ["/bin/bash", "--login", "-c"]
# # RUN echo "conda activate myenv" >> ~/.bashrc






