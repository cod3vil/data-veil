<template>
  <div id="app">
    <el-container class="app-container">
      <el-header class="app-header">
        <div class="header-content">
          <h1>文档脱敏平台</h1>
          <p class="header-subtitle">智能识别 · 安全脱敏 · 快速导出</p>
        </div>
      </el-header>
      
      <el-main class="app-main">
        <el-alert
          v-if="errorMessage"
          :title="errorMessage"
          type="error"
          :closable="true"
          @close="errorMessage = ''"
          show-icon
          class="error-alert"
        />

        <el-steps 
          :active="currentStep" 
          finish-status="success"
          align-center
          class="workflow-steps"
        >
          <el-step title="上传文档" icon="Upload" />
          <el-step title="配置规则" icon="Setting" />
          <el-step title="预览效果" icon="View" />
          <el-step title="导出下载" icon="Download" />
        </el-steps>

        <div class="content-container">
          <!-- 文件上传组件 -->
          <FileUpload
            ref="fileUploadRef"
            :api-base-url="apiBaseUrl"
            @upload-success="handleUploadSuccess"
            @upload-error="handleUploadError"
          />

          <!-- 规则配置组件 -->
          <RuleConfiguration
            ref="ruleConfigRef"
            :task-id="currentTaskId"
            :api-base-url="apiBaseUrl"
            @rules-changed="handleRulesChanged"
          />

          <!-- 预览对比组件 -->
          <PreviewComparison
            ref="previewRef"
            :task-id="currentTaskId"
            :selected-rules="selectedRules"
            :api-base-url="apiBaseUrl"
            @preview-ready="handlePreviewReady"
          />

          <!-- 导出下载组件 -->
          <ExportDownload
            ref="exportRef"
            :task-id="currentTaskId"
            :original-format="originalFormat"
            :selected-rules="selectedRules"
            :preview-ready="previewReady"
            :api-base-url="apiBaseUrl"
            @export-success="handleExportSuccess"
            @export-error="handleExportError"
          />
        </div>
      </el-main>

      <el-footer class="app-footer">
        <p>© 2025 文档脱敏平台 - 保护您的数据隐私</p>
      </el-footer>
    </el-container>

    <!-- 全局加载遮罩 -->
    <el-backtop :right="50" :bottom="50" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import FileUpload from './components/FileUpload.vue'
import RuleConfiguration from './components/RuleConfiguration.vue'
import PreviewComparison from './components/PreviewComparison.vue'
import ExportDownload from './components/ExportDownload.vue'

// API 基础 URL
const apiBaseUrl = ref('/api/v1')

// 组件引用
const fileUploadRef = ref(null)
const ruleConfigRef = ref(null)
const previewRef = ref(null)
const exportRef = ref(null)

// 状态管理
const currentTaskId = ref('')
const originalFormat = ref('')
const selectedRules = ref([])
const previewReady = ref(false)
const errorMessage = ref('')

// 当前步骤（用于步骤条显示）
const currentStep = computed(() => {
  if (!currentTaskId.value) return 0
  if (selectedRules.value.length === 0) return 1
  if (!previewReady.value) return 2
  return 3
})

// 处理文件上传成功
const handleUploadSuccess = (response) => {
  currentTaskId.value = response.task_id
  originalFormat.value = response.file_type
  previewReady.value = false
  
  ElNotification({
    title: '上传成功',
    message: `文件 ${response.filename} 已成功上传，请配置脱敏规则`,
    type: 'success',
    duration: 3000
  })
}

// 处理文件上传失败
const handleUploadError = (error) => {
  errorMessage.value = '文件上传失败，请检查文件格式和大小后重试'
  console.error('Upload error:', error)
}

// 处理规则变化
const handleRulesChanged = (rules) => {
  selectedRules.value = rules
  previewReady.value = false
  
  if (rules.length > 0) {
    ElMessage.success(`已选择 ${rules.length} 条脱敏规则`)
  }
}

// 处理预览生成成功
const handlePreviewReady = (previewData) => {
  previewReady.value = true
  
  ElNotification({
    title: '预览生成成功',
    message: `识别到 ${previewData.statistics.total_items} 处敏感信息，已脱敏 ${previewData.statistics.desensitized_items} 处`,
    type: 'success',
    duration: 3000
  })
}

// 处理导出成功
const handleExportSuccess = (data) => {
  ElNotification({
    title: '导出成功',
    message: `文件 ${data.filename} 已成功导出`,
    type: 'success',
    duration: 3000
  })
}

// 处理导出失败
const handleExportError = (error) => {
  errorMessage.value = '文件导出失败，请重试'
  console.error('Export error:', error)
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  background-color: #F5F7FA;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, #409EFF 0%, #3A8EE6 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  height: 120px !important;
}

.header-content {
  text-align: center;
}

.app-header h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 600;
  letter-spacing: 1px;
}

.header-subtitle {
  margin-top: 8px;
  font-size: 14px;
  opacity: 0.9;
  letter-spacing: 2px;
}

.app-main {
  flex: 1;
  padding: 30px 20px;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
}

.error-alert {
  margin-bottom: 20px;
}

.workflow-steps {
  margin-bottom: 30px;
  padding: 20px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.content-container {
  width: 100%;
}

.app-footer {
  background-color: #303133;
  color: #909399;
  text-align: center;
  padding: 20px;
  font-size: 14px;
  height: auto !important;
}

.app-footer p {
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-header h1 {
    font-size: 24px;
  }
  
  .header-subtitle {
    font-size: 12px;
  }
  
  .app-main {
    padding: 20px 10px;
  }
  
  .workflow-steps {
    padding: 15px 10px;
  }
}

/* 全局滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #F5F7FA;
}

::-webkit-scrollbar-thumb {
  background: #DCDFE6;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #C0C4CC;
}
</style>
