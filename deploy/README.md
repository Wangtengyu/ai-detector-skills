# AI内容检测器 API 部署指南

## 部署到 Zeabur（推荐）

### 步骤

1. **访问 Zeabur**：https://zeabur.com
2. **用 GitHub 登录**
3. **创建新项目**：
   - 点击 "New Project"
   - 选择 "Deploy from Git"
   - 选择你的 GitHub 仓库
   - 选择 `deploy` 目录
4. **配置环境变量**：
   - 在项目设置中添加：
     - `AI_PROVIDER` = `deepseek`
     - `AI_API_KEY` = `sk-eb51213b7bec4a5589536985e0d7a06e`
5. **部署**：点击 "Deploy"

### 部署完成后

- API地址格式：`https://你的项目名.zeabur.app/api/detect`
- 测试：访问 `https://你的项目名.zeabur.app/api/health`

---

## 部署到 Railway

### 步骤

1. **访问 Railway**：https://railway.app
2. **用 GitHub 登录**
3. **创建新项目**：
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的仓库
   - Root Directory 设置为 `deploy`
4. **添加环境变量**：
   - `AI_PROVIDER` = `deepseek`
   - `AI_API_KEY` = `sk-eb51213b7bec4a5589536985e0d7a06e`
5. **部署**

---

## 部署到 Render

### 步骤

1. **访问 Render**：https://render.com
2. **用 GitHub 登录**
3. **创建 Web Service**：
   - 选择你的仓库
   - Root Directory: `deploy`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT app:app`
4. **添加环境变量**：
   - `AI_PROVIDER` = `deepseek`
   - `AI_API_KEY` = `sk-eb51213b7bec4a5589536985e0d7a06e`
5. **部署**

---

## 更新前端 API 地址

部署完成后，修改前端页面的 API 地址：

```javascript
const apiUrl = 'https://你的域名/api/detect';
```

然后推送到 GitHub，GitHub Pages 会自动更新。
