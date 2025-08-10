FROM python:3.11-alpine

WORKDIR /app

# 复制代码
COPY app.py /app/app.py
COPY templates /app/templates
COPY events.json /app/events.json

# 安装 Flask + gunicorn
RUN pip install --no-cache-dir flask gunicorn

# 暴露端口
EXPOSE 5000

# 启动 gunicorn（绑定 0.0.0.0:5000）
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
