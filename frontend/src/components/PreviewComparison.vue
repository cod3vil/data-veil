<template>
  <el-card class="preview-card">
    <template #header>
      <div class="card-header">
        <span>脱敏预览</span>
        <div class="header-actions">
          <el-button 
            type="primary" 
            size="small" 
            @click="loadPreview"
            :loading="loading"
            :disabled="!taskId || !hasRules"
          >
            生成预览
          </el-button>
        </div>
      </div>
    </template>

    <div v-loading="loading" class="preview-content">
      <el-alert
        v-if="!taskId"
        title="请先上传文档并配置脱敏规则"
        type="info"
        :closable="false"
        show-icon
      />

      <div v-else-if="!hasRules" class="empty-state">
        <el-alert
          title="请至少选择一条脱敏规则"
          type="warning"
          :closable="false"
          show-icon
        />
      </div>

      <div v-else-if="!previewData && !loading" class="empty-state">
        <el-empty description='点击"生成预览"按钮查看脱敏效果' />
      </div>

      <div v-else-if="previewData" class="preview-container">
        <!-- 统计信息 -->
        <div class="statistics">
          <el-alert type="success" :closable="false">
            <template #default>
              <div class="stats-content">
                <span>识别到 <strong>{{ statistics.total_items }}</strong> 处敏感信息</span>
                <span>已脱敏 <strong>{{ statistics.desensitized_items }}</strong> 处</span>
              </div>
            </template>
          </el-alert>
        </div>

        <!-- 敏感信息列表 -->
        <div v-if="sensitiveItems.length > 0" class="sensitive-items">
          <el-collapse v-model="activeCollapse">
            <el-collapse-item title="敏感信息列表" name="items">
              <div class="items-list">
                <div 
                  v-for="(item, index) in sensitiveItems" 
                  :key="item.id"
                  class="item-row"
                  :class="{ 'item-disabled': !item.enabled }"
                >
                  <el-checkbox 
                    v-model="item.enabled"
                    @change="handleItemToggle(item)"
                  >
                    <div class="item-info">
                      <el-tag :type="getItemTagType(item.type)" size="small">
                        {{ getDataTypeLabel(item.type) }}
                      </el-tag>
                      <span class="item-value">{{ item.value }}</span>
                      <el-icon class="arrow-icon"><Right /></el-icon>
                      <span class="item-desensitized">{{ item.desensitized_value }}</span>
                    </div>
                  </el-checkbox>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- 对比视图 -->
        <div class="comparison-view">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="view-panel">
                <div class="panel-header">
                  <el-icon><Document /></el-icon>
                  <span>原始内容</span>
                </div>
                <div class="panel-content original-content">
                  <pre>{{ previewData.original }}</pre>
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="view-panel">
                <div class="panel-header desensitized-header">
                  <el-icon><Lock /></el-icon>
                  <span>脱敏后内容</span>
                </div>
                <div class="panel-content desensitized-content">
                  <pre v-html="highlightedDesensitized"></pre>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Lock, Right } from '@element-plus/icons-vue'
import axios from 'axios'

const props = defineProps({
  taskId: {
    type: String,
    default: ''
  },
  selectedRules: {
    type: Array,
    default: () => []
  },
  apiBaseUrl: {
    type: String,
    default: '/api/v1'
  }
})

const emit = defineEmits(['preview-ready'])

const loading = ref(false)
const previewData = ref(null)
const sensitiveItems = ref([])
const activeCollapse = ref(['items'])

const hasRules = computed(() => props.selectedRules.length > 0)

const statistics = computed(() => {
  if (!previewData.value) {
    return { total_items: 0, desensitized_items: 0 }
  }
  return previewData.value.statistics || { total_items: 0, desensitized_items: 0 }
})

const highlightedDesensitized = computed(() => {
  if (!previewData.value) return ''
  
  let content = previewData.value.desensitized
  
  // 高亮显示脱敏位置（简单实现，用黄色背景标记）
  // 在实际应用中，可以根据 sensitiveItems 的位置信息进行更精确的高亮
  sensitiveItems.value.forEach(item => {
    if (item.enabled && item.desensitized_value) {
      const regex = new RegExp(escapeRegExp(item.desensitized_value), 'g')
      content = content.replace(regex, `<mark class="highlight">${item.desensitized_value}</mark>`)
    }
  })
  
  return content
})

// 监听规则变化，清空预览
watch(() => props.selectedRules, () => {
  if (previewData.value) {
    ElMessage.info('规则已更改，请重新生成预览')
  }
})

const loadPreview = async () => {
  if (!props.taskId || !hasRules.value) {
    return
  }

  loading.value = true
  try {
    // 首先识别敏感信息
    await identifySensitiveData()
    
    // 然后生成预览
    const response = await axios.post(
      `${props.apiBaseUrl}/tasks/${props.taskId}/preview`,
      {
        rules: props.selectedRules,
        sensitive_items: sensitiveItems.value
          .filter(item => item.enabled)
          .map(item => item.id)
      }
    )
    
    previewData.value = response.data
    
    ElMessage.success('预览生成成功')
    emit('preview-ready', previewData.value)
  } catch (error) {
    console.error('生成预览失败:', error)
    const errorMsg = error.response?.data?.message || '生成预览失败，请重试'
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}

const identifySensitiveData = async () => {
  try {
    const response = await axios.post(
      `${props.apiBaseUrl}/tasks/${props.taskId}/identify`,
      { use_nlp: true }
    )
    
    // 初始化敏感信息列表，默认全部启用
    sensitiveItems.value = (response.data.sensitive_items || []).map(item => ({
      ...item,
      enabled: true,
      desensitized_value: '' // 将在预览时填充
    }))
  } catch (error) {
    console.error('识别敏感信息失败:', error)
    throw error
  }
}

const handleItemToggle = (item) => {
  // 当用户切换某个敏感项的启用状态时，需要重新生成预览
  ElMessage.info('请重新生成预览以查看更改效果')
}

const getDataTypeLabel = (dataType) => {
  const labels = {
    'name': '姓名',
    'id_card': '身份证',
    'phone': '手机号',
    'address': '地址',
    'bank_card': '银行卡',
    'email': '邮箱'
  }
  return labels[dataType] || dataType
}

const getItemTagType = (dataType) => {
  const types = {
    'name': 'primary',
    'id_card': 'success',
    'phone': 'warning',
    'address': 'info',
    'bank_card': 'danger',
    'email': ''
  }
  return types[dataType] || ''
}

const escapeRegExp = (string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// 暴露方法供父组件调用
defineExpose({
  loadPreview,
  getPreviewData: () => previewData.value
})
</script>

<style scoped>
.preview-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.preview-content {
  min-height: 300px;
}

.empty-state {
  padding: 40px 0;
}

.preview-container {
  width: 100%;
}

.statistics {
  margin-bottom: 20px;
}

.stats-content {
  display: flex;
  gap: 30px;
  font-size: 14px;
}

.stats-content strong {
  color: #409EFF;
  font-size: 16px;
}

.sensitive-items {
  margin-bottom: 20px;
}

.items-list {
  max-height: 300px;
  overflow-y: auto;
}

.item-row {
  padding: 10px;
  border-bottom: 1px solid #EBEEF5;
  transition: background-color 0.3s;
}

.item-row:hover {
  background-color: #F5F7FA;
}

.item-row:last-child {
  border-bottom: none;
}

.item-row.item-disabled {
  opacity: 0.5;
}

.item-row :deep(.el-checkbox__label) {
  width: 100%;
}

.item-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.item-value {
  color: #303133;
  font-weight: 500;
}

.arrow-icon {
  color: #909399;
}

.item-desensitized {
  color: #67C23A;
  font-family: 'Courier New', monospace;
}

.comparison-view {
  width: 100%;
}

.view-panel {
  border: 1px solid #DCDFE6;
  border-radius: 4px;
  overflow: hidden;
}

.panel-header {
  background-color: #F5F7FA;
  padding: 12px 15px;
  font-weight: 500;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #DCDFE6;
}

.desensitized-header {
  background-color: #F0F9FF;
  color: #409EFF;
}

.panel-content {
  padding: 15px;
  background-color: #FFFFFF;
  max-height: 500px;
  overflow-y: auto;
}

.panel-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #303133;
}

.original-content pre {
  color: #606266;
}

.desensitized-content :deep(mark.highlight) {
  background-color: #FFF3CD;
  color: #856404;
  padding: 2px 4px;
  border-radius: 2px;
  font-weight: 500;
}
</style>
