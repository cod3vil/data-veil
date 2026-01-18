<template>
  <el-card class="export-card">
    <template #header>
      <div class="card-header">
        <span>导出下载</span>
      </div>
    </template>

    <div class="export-content">
      <el-alert
        v-if="!taskId"
        title="请先完成文档上传和脱敏预览"
        type="info"
        :closable="false"
        show-icon
      />

      <div v-else class="export-options">
        <div class="format-selection">
          <div class="section-title">
            <el-icon><Document /></el-icon>
            <span>选择导出格式</span>
          </div>
          
          <el-radio-group v-model="selectedFormat" class="format-group">
            <el-radio 
              v-for="format in availableFormats" 
              :key="format.value"
              :label="format.value"
              :disabled="!format.available"
            >
              <div class="format-option">
                <span class="format-name">{{ format.label }}</span>
                <span class="format-desc">{{ format.description }}</span>
              </div>
            </el-radio>
          </el-radio-group>
        </div>

        <el-divider />

        <div class="export-actions">
          <el-button
            type="primary"
            size="large"
            :loading="exporting"
            :disabled="!canExport"
            @click="handleExport"
          >
            <el-icon v-if="!exporting"><Download /></el-icon>
            {{ exporting ? '正在导出...' : '导出并下载' }}
          </el-button>
          
          <div v-if="exportHistory.length > 0" class="export-history">
            <div class="section-title">
              <el-icon><Clock /></el-icon>
              <span>导出历史</span>
            </div>
            <div class="history-list">
              <div 
                v-for="(item, index) in exportHistory" 
                :key="index"
                class="history-item"
              >
                <div class="history-info">
                  <el-tag size="small" type="success">{{ item.format.toUpperCase() }}</el-tag>
                  <span class="history-filename">{{ item.filename }}</span>
                  <span class="history-time">{{ formatTime(item.time) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Download, Clock } from '@element-plus/icons-vue'
import axios from 'axios'

const props = defineProps({
  taskId: {
    type: String,
    default: ''
  },
  originalFormat: {
    type: String,
    default: ''
  },
  selectedRules: {
    type: Array,
    default: () => []
  },
  previewReady: {
    type: Boolean,
    default: false
  },
  apiBaseUrl: {
    type: String,
    default: '/api/v1'
  }
})

const emit = defineEmits(['export-success', 'export-error'])

const selectedFormat = ref('original')
const exporting = ref(false)
const exportHistory = ref([])

// 根据原始格式确定可用的导出格式
const availableFormats = computed(() => {
  const formats = [
    {
      value: 'original',
      label: '原格式',
      description: '保持与上传文档相同的格式',
      available: true
    },
    {
      value: 'md',
      label: 'Markdown',
      description: '导出为 Markdown 格式，适合文档编辑',
      available: true
    }
  ]

  // 根据原始格式添加特定格式选项
  if (props.originalFormat === 'pdf') {
    formats[0].label = 'TXT'
    formats[0].description = 'PDF 将导出为纯文本格式'
  } else if (props.originalFormat === 'docx') {
    formats[0].label = 'DOCX'
  } else if (props.originalFormat === 'xlsx') {
    formats[0].label = 'XLSX'
  } else if (props.originalFormat === 'txt') {
    formats[0].label = 'TXT'
  }

  return formats
})

const canExport = computed(() => {
  return props.taskId && props.selectedRules.length > 0 && props.previewReady
})

// 监听原始格式变化，自动选择默认格式
watch(() => props.originalFormat, (newFormat) => {
  if (newFormat) {
    selectedFormat.value = 'original'
  }
})

const handleExport = async () => {
  if (!canExport.value) {
    ElMessage.warning('请先完成文档上传、规则配置和预览生成')
    return
  }

  exporting.value = true
  try {
    // 确定实际的输出格式
    let outputFormat = selectedFormat.value
    if (outputFormat === 'original') {
      outputFormat = props.originalFormat === 'pdf' ? 'txt' : props.originalFormat
    }

    const response = await axios.post(
      `${props.apiBaseUrl}/tasks/${props.taskId}/export`,
      {
        rules: props.selectedRules,
        output_format: outputFormat
      },
      {
        responseType: 'blob'
      }
    )

    // 从响应头获取文件名
    const contentDisposition = response.headers['content-disposition']
    let filename = `desensitized_${Date.now()}.${outputFormat}`
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '')
      }
    }

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    // 添加到导出历史
    exportHistory.value.unshift({
      filename,
      format: outputFormat,
      time: new Date().toISOString()
    })

    // 只保留最近5条记录
    if (exportHistory.value.length > 5) {
      exportHistory.value = exportHistory.value.slice(0, 5)
    }

    ElMessage.success('文件导出成功！')
    emit('export-success', { filename, format: outputFormat })
  } catch (error) {
    console.error('导出失败:', error)
    const errorMsg = error.response?.data?.message || '文件导出失败，请重试'
    ElMessage.error(errorMsg)
    emit('export-error', error)
  } finally {
    exporting.value = false
  }
}

const formatTime = (timeString) => {
  const date = new Date(timeString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 暴露方法供父组件调用
defineExpose({
  exportFile: handleExport,
  clearHistory: () => {
    exportHistory.value = []
  }
})
</script>

<style scoped>
.export-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: bold;
  font-size: 16px;
}

.export-content {
  min-height: 200px;
}

.export-options {
  width: 100%;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 15px;
}

.format-selection {
  margin-bottom: 20px;
}

.format-group {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.format-group :deep(.el-radio) {
  margin-right: 0;
  padding: 15px;
  border: 1px solid #DCDFE6;
  border-radius: 4px;
  transition: all 0.3s;
}

.format-group :deep(.el-radio:hover) {
  border-color: #409EFF;
  background-color: #F5F7FA;
}

.format-group :deep(.el-radio.is-checked) {
  border-color: #409EFF;
  background-color: #ECF5FF;
}

.format-group :deep(.el-radio__label) {
  width: 100%;
}

.format-option {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.format-name {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
}

.format-desc {
  font-size: 12px;
  color: #909399;
}

.export-actions {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.export-actions .el-button {
  width: 100%;
}

.export-history {
  margin-top: 10px;
}

.history-list {
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  padding: 10px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  margin-bottom: 8px;
  background-color: #FAFAFA;
}

.history-item:last-child {
  margin-bottom: 0;
}

.history-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.history-filename {
  flex: 1;
  color: #303133;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-time {
  color: #909399;
  font-size: 12px;
}
</style>
