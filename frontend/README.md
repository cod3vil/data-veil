# 文档脱敏平台 - 前端

基于 Vue 3 + Element Plus 构建的文档脱敏平台前端应用。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Element Plus** - Vue 3 UI 组件库
- **Axios** - HTTP 客户端
- **Vite** - 前端构建工具

## 项目结构

```
frontend/
├── src/
│   ├── components/          # 组件目录
│   │   ├── FileUpload.vue          # 文件上传组件
│   │   ├── RuleConfiguration.vue   # 规则配置组件
│   │   ├── PreviewComparison.vue   # 预览对比组件
│   │   └── ExportDownload.vue      # 导出下载组件
│   ├── App.vue             # 主应用组件
│   └── main.js             # 应用入口
├── index.html              # HTML 模板
├── vite.config.js          # Vite 配置
└── package.json            # 项目依赖

```

## 组件说明

### 1. FileUpload.vue - 文件上传组件

**功能特性：**
- 拖拽上传支持
- 文件格式验证（PDF、DOCX、XLSX、TXT、MD）
- 文件大小验证（最大 50MB）
- 上传进度显示
- 上传成功/失败提示

**事件：**
- `upload-success`: 上传成功时触发，返回任务信息
- `upload-error`: 上传失败时触发

### 2. RuleConfiguration.vue - 规则配置组件

**功能特性：**
- 显示预配置的脱敏规则列表
- 支持规则启用/禁用选择
- 全选/取消全选功能
- 显示规则详情（数据类型、策略、示例）

**事件：**
- `rules-changed`: 规则选择变化时触发，返回选中的规则 ID 列表

### 3. PreviewComparison.vue - 预览对比组件

**功能特性：**
- 左右对比视图显示原文和脱敏后内容
- 高亮显示脱敏位置
- 显示敏感信息列表
- 支持手动调整敏感项的启用状态
- 显示识别统计信息

**事件：**
- `preview-ready`: 预览生成成功时触发，返回预览数据

### 4. ExportDownload.vue - 导出下载组件

**功能特性：**
- 支持多种导出格式选择（原格式、Markdown）
- 一键导出并下载
- 显示导出历史记录
- 导出进度提示

**事件：**
- `export-success`: 导出成功时触发
- `export-error`: 导出失败时触发

## 开发指南

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

应用将在 http://localhost:5173 启动，并自动代理 API 请求到后端（http://localhost:8000）。

### 生产构建

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 预览生产构建

```bash
npm run preview
```

## 工作流程

1. **上传文档** - 用户通过拖拽或点击上传文档
2. **配置规则** - 选择需要应用的脱敏规则
3. **预览效果** - 生成并查看脱敏前后的对比
4. **导出下载** - 选择格式并导出脱敏后的文档

## API 集成

前端通过 Axios 与后端 API 通信，所有 API 请求都通过 `/api/v1` 前缀。

主要 API 端点：
- `POST /api/v1/upload` - 上传文档
- `GET /api/v1/rules` - 获取脱敏规则
- `POST /api/v1/tasks/{task_id}/identify` - 识别敏感信息
- `POST /api/v1/tasks/{task_id}/preview` - 生成预览
- `POST /api/v1/tasks/{task_id}/export` - 导出文档

## 样式说明

- 使用 Element Plus 默认主题
- 主色调：#409EFF（蓝色）
- 响应式设计，支持移动端访问
- 自定义滚动条样式

## 浏览器支持

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 注意事项

1. 确保后端 API 服务已启动（默认端口 8000）
2. 开发模式下，Vite 会自动代理 API 请求
3. 生产环境需要配置 Nginx 反向代理
4. 文件上传大小限制为 50MB
