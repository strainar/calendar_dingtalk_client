# Docker部署后访问API文档的两种方式

## 方式1: 通过动态生成的OpenAPI端点

应用启动后，可以通过以下URL访问 Swagger UI：

```
http://192.168.1.204:8000/docs
```

或 ReDoc 格式文档：

```
http://192.168.1.204:8000/redoc
```

---

## 方式2: 使用预生成的静态OpenAPI Schema文件

### 在本地生成静态Schema文件

```bash
cd docker.version

# 安装依赖
pip install pyyaml

# 生成OpenAPI 3.1.0 Schema
python generate_openapi_schema.py
```

### 生成的文件

执行后会生成以下文件：

```
docker.version/api_schema/
├── openapi.json      # OpenAPI 3.1.0 JSON格式
├── openapi.yaml      # OpenAPI 3.1.0 YAML格式
└── index.html        # Swagger UI静态页面（可选）
```

### 使用静态文件

#### 选项A: 复制到HTTP服务器

将 `api_schema/` 目录复制到任何静态文件服务器：

```bash
# 例如使用 Python内置服务器
cd docker.version/api_schema
python -m http.server 8080
# 访问 http://localhost:8080
```

#### 选项B: 在Docker中运行Swagger UI

更新 `docker-compose.yml` 添加 Nginx 服务：

```yaml
services:
  calendar-app:
    image: calendar-dingtalk-client:latest
    network_mode: host

  swagger-ui:
    image: swaggerapi/swagger-ui:latest
    ports:
      - "8081:8080"
    environment:
      - SWAGGER_JSON=/schema/openapi.json
    volumes:
      - ./api_schema/openapi.json:/schema/openapi.json:ro
```

---

## 方式3: 导出为其他格式

### Postman Collection

```bash
# 使用 redocly 命令行工具
npm install -g @redocly/cli@latest

redocly openapi2postmanv2 api_schema/openapi.json > calendar-api.postman.json
```

### API Blueprint

```bash
npm install -g aglio

aglio -i api_schema/openapi.json -o api_docs.html
```

---

## 验证OpenAPI Schema合规性

```bash
# 安装 OpenAPI linter
pip install openapi-spec-validator

python -c "
from openapi_spec_validator import validate
import json

with open('api_schema/openapi.json') as f:
    spec = json.load(f)
    
validate(spec)
print('✅ OpenAPI 3.1.0 Schema 验证通过')
"
```

---

## 推荐的API文档工具

| 工具 | 特点 | 访问方式 |
|------|------|----------|
| Swagger UI | 交互式API测试 | /docs |
| ReDoc | 精美的文档展示 | /redoc |
| RapiDoc | Web组件风格 | 自部署 |
| Stoplight Studio | 桌面 IDE | 独立应用 |
