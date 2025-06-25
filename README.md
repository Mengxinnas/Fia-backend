# Fia财务分析后端API

## 项目简介

这是Fia金融智能助手的Python后端服务，提供文件上传、文档解析、向量化存储、智能问答和财务分析等功能。

## 主要功能

- 📄 多格式文件解析（PDF、Word、Excel、CSV、TXT）
- 🔍 智能文档搜索和问答
- 📊 财务分析报告生成
- 💾 向量化文档存储
- 🚀 RESTful API接口

## 技术栈

- **Web框架**: FastAPI
- **文件解析**: PyMuPDF, python-docx, pandas, openpyxl
- **向量化**: scikit-learn, faiss-cpu, jieba
- **AI服务**: DeepSeek API
- **部署**: Render.com

## 项目结构

```
python-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置设置
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # 数据模型
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── upload.py        # 文件上传路由
│   │   ├── qa.py           # 问答路由
│   │   └── financial.py    # 财务分析路由
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_parser.py   # 文件解析服务
│   │   ├── vector_service.py # 向量化服务
│   │   ├── qa_service.py    # 问答服务
│   │   └── financial_service.py # 财务分析服务
│   └── utils/
│       ├── __init__.py
│       └── helpers.py       # 工具函数
├── requirements.txt         # Python依赖
├── gunicorn.conf.py        # Gunicorn配置
├── render.yaml             # Render部署配置
└── README.md               # 项目说明
```

## 本地开发

### 环境要求
- Python 3.11+
- pip

### 安装依赖
```bash
pip install -r requirements.txt
```

### 环境变量配置
创建 `.env` 文件：
```env
DEEPSEEK_API_KEY=your_deepseek_api_key
DEBUG=true
```

### 运行开发服务器
```bash
python app/main.py
```

或使用uvicorn：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API文档
启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Render部署

### 1. 创建GitHub仓库
将此目录上传到GitHub仓库

### 2. 在Render创建Web Service
1. 访问 [Render.com](https://render.com)
2. 连接GitHub仓库
3. 选择 "Web Service"
4. 配置构建设置：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

### 3. 环境变量配置
在Render控制台设置：
- `DEEPSEEK_API_KEY`: DeepSeek API密钥
- `PYTHON_VERSION`: 3.11

### 4. 部署
点击部署，等待构建完成

## API接口

### 文件上传
```
POST /api/upload
Content-Type: multipart/form-data

上传文件并进行向量化处理
```

### 智能问答
```
POST /api/qa/ask
Content-Type: application/json

{
  "text": "用户问题"
}
```

### 财务分析
```
POST /api/financial-analysis
Content-Type: application/json

{
  "analysis_type": "comprehensive",
  "company_name": "企业名称"
}
```

### 系统状态
```
GET /status

获取系统运行状态和文档统计
```

## 前端集成

在Next.js项目中更新API配置：

```typescript
// 更新API基础URL
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://your-render-app.onrender.com'
  : 'http://localhost:8000';
```

## 注意事项

1. **文件限制**: 最大支持50MB文件
2. **支持格式**: PDF, DOCX, XLSX, CSV, TXT
3. **并发限制**: 建议不超过5个并发任务
4. **临时文件**: 使用/tmp目录，会自动清理
5. **API密钥**: 确保DeepSeek API密钥配置正确

## 故障排除

### 常见问题
1. **依赖安装失败**: 确保Python版本为3.11+
2. **文件解析错误**: 检查文件格式和编码
3. **AI服务调用失败**: 验证API密钥配置
4. **内存不足**: Render免费版内存有限，考虑升级

### 日志查看
在Render控制台查看实时日志，或本地运行时查看控制台输出

## 许可证

MIT License
```

现在整个Python后端部署结构已经创建完成！你可以将 `python-backend` 目录上传到GitHub，然后在Render上部署。部署成功后，记得更新Vercel上的Next.js项目中的API端点配置。 