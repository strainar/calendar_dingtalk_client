# 修改docker-compose.yml使用现有镜像而不是重新构建
sed -i 's/build: \./image: calendar-dingtalk-client:latest/' docker-compose.yml