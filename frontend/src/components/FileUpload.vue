<template>
  <el-card class="upload-card">
    <template #header>
      <div class="card-header">
        <span>文档上传</span>
      </div>
    </template>
    
    <el-upload
      ref="uploadRef"
      class="upload-area"
      drag
      :action="uploadUrl"
      :before-upload="beforeUpload"
      :on-progress="handleProgress"
      :on-success="handleSuccess"
      :on-error="handleError"
      :show-file-list="false"
      :auto-upload="true"
      accept=".pdf,.docx,.xlsx,.txt,.md"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        将文件拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持格式：PDF、DOCX、XLSX、TXT、MD，文件大小不超过 50MB
        </div>
      </template>
    </el-upload>

    <div v-if="uploading" class="upload-progress">
      <el-progress :percentage="uploadProgress" :status="progressStatus" />
      <p class="progress-text">{{ progressText }}</p>
    </div>

    <div v-if="uploadedFile" class="uploaded-file">
      <el-alert
        :title="`文件上传成功：${uploadedFile.filename}`"
        type="success"
        :closable="false"
        show-icon
      >
        <template #default>
          <p>文件大小：{{ formatFileSize(uploadedFile.file_size) }}</p>
          <p>上传时间：{{ formatTime(uploadedFile.upload_time) }}</p>
        </template>
      </el-alert>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const props = defineProps({
  apiBaseUrl: {
    type: String,
    default: '/api/v1'
  }
})

const emit = defineEmits(['upload-success', 'upload-error'])

const uploadRef = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const progressStatus = ref('')
const progressText = ref('')
const uploadedFile = ref(null)

const uploadUrl = computed(() => `${props.apiBaseUrl}/upload`)

// 文件格式验证
const ALLOWED_FORMATS = ['pdf', 'docx', 'xlsx', 'txt', 'md']
const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB

const beforeUpload = (file) => {
  // 验证文件格式
  const fileExtension = file.name.split('.').pop().toLowerCase()
  if (!ALLOWED_FORMATS.includes(fileExtension)) {
    ElMessage.error(`不支持的文件格式：${fileExtension}。支持的格式：${ALLOWED_FORMATS.join('、')}`)
    return false
  }

  // 验证文件大小
  if (file.size > MAX_FILE_SIZE) {
    ElMessage.error(`文件大小超过限制。最大允许 50MB，当前文件：${formatFileSize(file.size)}`)
    return false
  }

  uploading.value = true
  uploadProgress.value = 0
  progressStatus.value = ''
  progressText.value = '正在上传...'
  uploadedFile.value = null

  return true
}

const handleProgress = (event, file) => {
  uploadProgress.value = Math.floor(event.percent)
  progressText.value = `正在上传... ${uploadProgress.value}%`
}

const handleSuccess = (response, file) => {
  uploading.value = false
  uploadProgress.value = 100
  progressStatus.value = 'success'
  progressText.value = '上传完成！'
  
  uploadedFile.value = response
  
  ElMessage.success('文件上传成功！')
  emit('upload-success', response)
}

const handleError = (error, file) => {
  uploading.value = false
  progressStatus.value = 'exception'
  progressText.value = '上传失败'
  
  let errorMessage = '文件上传失败'
  try {
    const errorData = JSON.parse(error.message)
    errorMessage = errorData.message || errorMessage
  } catch (e) {
    // 使用默认错误消息
  }
  
  ElMessage.error(errorMessage)
  emit('upload-error', error)
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatTime = (timeString) => {
  const date = new Date(timeString)
  return date.toLocaleString('zh-CN')
}

// 暴露方法供父组件调用
defineExpose({
  clearFiles: () => {
    uploadedFile.value = null
    uploading.value = false
    uploadProgress.value = 0
  }
})
</script>

<style scoped>
.upload-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: bold;
  font-size: 16px;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  padding: 40px;
}

.el-icon--upload {
  font-size: 67px;
  color: #409EFF;
  margin-bottom: 16px;
}

.el-upload__text {
  font-size: 14px;
  color: #606266;
}

.el-upload__text em {
  color: #409EFF;
  font-style: normal;
}

.el-upload__tip {
  font-size: 12px;
  color: #909399;
  margin-top: 7px;
  text-align: center;
}

.upload-progress {
  margin-top: 20px;
}

.progress-text {
  text-align: center;
  margin-top: 10px;
  color: #606266;
  font-size: 14px;
}

.uploaded-file {
  margin-top: 20px;
}

.uploaded-file :deep(.el-alert__content) {
  width: 100%;
}

.uploaded-file p {
  margin: 5px 0;
  font-size: 13px;
}
</style>
