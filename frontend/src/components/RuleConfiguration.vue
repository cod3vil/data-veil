<template>
  <el-card class="rule-card">
    <template #header>
      <div class="card-header">
        <span>脱敏规则配置</span>
        <el-button 
          type="primary" 
          size="small" 
          @click="loadRules"
          :loading="loading"
        >
          刷新规则
        </el-button>
      </div>
    </template>

    <div v-loading="loading" class="rule-content">
      <el-alert
        v-if="!taskId"
        title="请先上传文档"
        type="info"
        :closable="false"
        show-icon
      />

      <div v-else-if="rules.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无可用规则" />
      </div>

      <div v-else class="rules-list">
        <div class="rules-header">
          <el-checkbox 
            v-model="selectAll" 
            @change="handleSelectAll"
            :indeterminate="isIndeterminate"
          >
            全选
          </el-checkbox>
          <span class="selected-count">
            已选择 {{ selectedRules.length }} / {{ rules.length }} 条规则
          </span>
        </div>

        <el-divider />

        <el-checkbox-group v-model="selectedRules" @change="handleSelectionChange">
          <div v-for="rule in rules" :key="rule.id" class="rule-item">
            <el-checkbox :label="rule.id">
              <div class="rule-info">
                <div class="rule-name">
                  <el-tag :type="getTagType(rule.data_type)" size="small">
                    {{ getDataTypeLabel(rule.data_type) }}
                  </el-tag>
                  <span class="name-text">{{ rule.name }}</span>
                </div>
                <div class="rule-details">
                  <span class="strategy">
                    策略：{{ getStrategyLabel(rule.strategy) }}
                  </span>
                  <span class="example">
                    示例：{{ getExample(rule.data_type, rule.strategy) }}
                  </span>
                </div>
              </div>
            </el-checkbox>
          </div>
        </el-checkbox-group>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const props = defineProps({
  taskId: {
    type: String,
    default: ''
  },
  apiBaseUrl: {
    type: String,
    default: '/api/v1'
  }
})

const emit = defineEmits(['rules-changed'])

const loading = ref(false)
const rules = ref([])
const selectedRules = ref([])
const selectAll = ref(false)

const isIndeterminate = computed(() => {
  const selectedCount = selectedRules.value.length
  return selectedCount > 0 && selectedCount < rules.value.length
})

// 监听 taskId 变化，自动加载规则
watch(() => props.taskId, (newTaskId) => {
  if (newTaskId) {
    loadRules()
  }
}, { immediate: true })

const loadRules = async () => {
  if (!props.taskId) {
    return
  }

  loading.value = true
  try {
    const response = await axios.get(`${props.apiBaseUrl}/rules`)
    rules.value = response.data.rules || []
    
    // 默认选中所有启用的规则
    selectedRules.value = rules.value
      .filter(rule => rule.enabled)
      .map(rule => rule.id)
    
    selectAll.value = selectedRules.value.length === rules.value.length
    
    emit('rules-changed', selectedRules.value)
  } catch (error) {
    console.error('加载规则失败:', error)
    ElMessage.error('加载脱敏规则失败，请重试')
  } finally {
    loading.value = false
  }
}

const handleSelectAll = (checked) => {
  if (checked) {
    selectedRules.value = rules.value.map(rule => rule.id)
  } else {
    selectedRules.value = []
  }
  emit('rules-changed', selectedRules.value)
}

const handleSelectionChange = (value) => {
  selectAll.value = value.length === rules.value.length
  emit('rules-changed', value)
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

const getStrategyLabel = (strategy) => {
  const labels = {
    'mask': '掩码',
    'replace': '替换',
    'delete': '删除'
  }
  return labels[strategy] || strategy
}

const getTagType = (dataType) => {
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

const getExample = (dataType, strategy) => {
  const examples = {
    'name': {
      'mask': '张三 → 张*',
      'replace': '张三 → [姓名]',
      'delete': '张三 → '
    },
    'id_card': {
      'mask': '110101199001011234 → 110101********1234',
      'replace': '110101199001011234 → [身份证]',
      'delete': '110101199001011234 → '
    },
    'phone': {
      'mask': '13812345678 → 138****5678',
      'replace': '13812345678 → [电话]',
      'delete': '13812345678 → '
    },
    'address': {
      'mask': '北京市朝阳区XX路10号 → 北京市朝阳区******',
      'replace': '北京市朝阳区XX路10号 → [地址]',
      'delete': '北京市朝阳区XX路10号 → '
    },
    'bank_card': {
      'mask': '6222021234567890123 → 6222************123',
      'replace': '6222021234567890123 → [银行卡]',
      'delete': '6222021234567890123 → '
    },
    'email': {
      'mask': 'user@example.com → u***@example.com',
      'replace': 'user@example.com → [邮箱]',
      'delete': 'user@example.com → '
    }
  }
  return examples[dataType]?.[strategy] || ''
}

// 暴露方法供父组件调用
defineExpose({
  getSelectedRules: () => selectedRules.value,
  loadRules
})
</script>

<style scoped>
.rule-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 16px;
}

.rule-content {
  min-height: 200px;
}

.empty-state {
  padding: 40px 0;
}

.rules-list {
  width: 100%;
}

.rules-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.selected-count {
  font-size: 14px;
  color: #909399;
}

.rule-item {
  padding: 12px 0;
  border-bottom: 1px solid #EBEEF5;
}

.rule-item:last-child {
  border-bottom: none;
}

.rule-item :deep(.el-checkbox) {
  width: 100%;
  align-items: flex-start;
}

.rule-item :deep(.el-checkbox__label) {
  width: 100%;
  white-space: normal;
}

.rule-info {
  width: 100%;
  padding-left: 10px;
}

.rule-name {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.name-text {
  margin-left: 10px;
  font-weight: 500;
  font-size: 14px;
  color: #303133;
}

.rule-details {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 13px;
  color: #606266;
}

.strategy {
  color: #909399;
}

.example {
  color: #67C23A;
  font-family: 'Courier New', monospace;
}
</style>
