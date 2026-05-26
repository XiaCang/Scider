<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete, Edit } from '@element-plus/icons-vue'
import { getProvidersApi, createProviderApi, updateProviderApi, deleteProviderApi } from '../../../api/settings'
import type { ModelProvider, CreateProviderPayload } from '../../../types/settings'

const loading = ref(true)
const providers = ref<ModelProvider[]>([])
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const editingMaskedKey = ref('')
const dialogLoading = ref(false)
const dialogFormRef = ref<FormInstance>()

const dialogForm = reactive({
  name: '',
  provider: 'openai',
  base_url: '',
  api_key: '',
  default_model: '',
  enabled: true,
})

const PROVIDER_OPTIONS = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Google', value: 'google' },
  { label: 'Azure', value: 'azure' },
  { label: '自定义', value: 'custom' },
]

const PROVIDER_BASE_URLS: Record<string, string> = {
  openai: 'https://api.openai.com',
  anthropic: 'https://api.anthropic.com',
  google: 'https://generativelanguage.googleapis.com',
  azure: '',
  custom: '',
}

const isEditing = computed(() => editingId.value !== null)

const dialogTitle = computed(() =>
  isEditing.value ? '编辑提供商' : '添加提供商'
)

const dialogRules: FormRules = {
  name: [
    { required: true, message: '请输入提供商名称', trigger: 'blur' },
  ],
  provider: [
    { required: true, message: '请选择提供商类型', trigger: 'change' },
  ],
  api_key: [
    { required: true, message: '请输入 API Key', trigger: 'blur' },
  ],
  base_url: [
    { required: true, message: '请输入 API 地址', trigger: 'blur' },
  ],
  default_model: [
    { required: true, message: '请输入默认模型', trigger: 'blur' },
  ],
}

const fetchProviders = async () => {
  loading.value = true
  try {
    const response = await getProvidersApi()
    providers.value = response.data || []
  } catch (error) {
    ElMessage.error('获取模型提供商列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleProviderChange = (val: string) => {
  const url = PROVIDER_BASE_URLS[val]
  if (url && !dialogForm.base_url) {
    dialogForm.base_url = url
  }
  // 根据提供商类型给出默认模型建议
  const modelHints: Record<string, string> = {
    openai: 'gpt-4o',
    anthropic: 'claude-sonnet-4-6',
    google: 'gemini-2.0-flash',
  }
  if (modelHints[val] && !dialogForm.default_model) {
    dialogForm.default_model = modelHints[val]
  }
}

const openAddDialog = () => {
  editingId.value = null
  editingMaskedKey.value = ''
  dialogForm.name = ''
  dialogForm.provider = 'openai'
  dialogForm.base_url = PROVIDER_BASE_URLS['openai']
  dialogForm.api_key = ''
  dialogForm.default_model = 'gpt-4o'
  dialogForm.enabled = true
  dialogVisible.value = true
}

const openEditDialog = (provider: ModelProvider) => {
  editingId.value = provider.id
  editingMaskedKey.value = provider.api_key_masked
  dialogForm.name = provider.name
  dialogForm.provider = provider.provider
  dialogForm.base_url = provider.base_url
  dialogForm.api_key = ''
  dialogForm.default_model = provider.default_model
  dialogForm.enabled = provider.enabled
  dialogVisible.value = true
}

const handleDialogSubmit = async () => {
  if (!dialogFormRef.value) return
  await dialogFormRef.value.validate(async (valid) => {
    if (!valid) return

    dialogLoading.value = true
    try {
      if (isEditing.value) {
        await updateProviderApi(editingId.value!, {
          name: dialogForm.name,
          base_url: dialogForm.base_url,
          api_key: dialogForm.api_key || undefined,
          enabled: dialogForm.enabled,
        })
        ElMessage.success('提供商已更新')
      } else {
        const payload: CreateProviderPayload = {
          name: dialogForm.name,
          provider: dialogForm.provider,
          base_url: dialogForm.base_url,
          api_key: dialogForm.api_key,
          default_model: dialogForm.default_model,
          enabled: dialogForm.enabled,
        }
        await createProviderApi(payload)
        ElMessage.success('提供商已添加')
      }
      dialogVisible.value = false
      await fetchProviders()
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '操作失败')
    } finally {
      dialogLoading.value = false
    }
  })
}

const toggleEnabled = async (provider: ModelProvider) => {
  try {
    await updateProviderApi(provider.id, {
      enabled: !provider.enabled,
    })
    await fetchProviders()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '操作失败')
  }
}

const handleDelete = async (provider: ModelProvider) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除提供商"${provider.name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      }
    )
    await deleteProviderApi(provider.id)
    ElMessage.success('提供商已删除')
    await fetchProviders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error instanceof Error ? error.message : '删除失败')
    }
  }
}

/** 掩码显示 API Key */
const maskApiKey = (key: string): string => {
  if (!key) return '••••••••'
  return key
}

onMounted(() => {
  fetchProviders()
})
</script>

<template>
  <div class="settings-section">
    <div class="section-header">
      <div class="section-header-row">
        <div>
          <h3 class="section-title">模型提供商</h3>
          <p class="section-desc">管理 AI 模型服务商，可添加多个提供商及其 API 凭据</p>
        </div>
        <el-button type="primary" :icon="Plus" @click="openAddDialog">
          添加提供商
        </el-button>
      </div>
    </div>

    <div class="section-body" v-loading="loading">
      <!-- 空状态 -->
      <div v-if="!loading && providers.length === 0" class="empty-state">
        <el-icon :size="48" class="empty-icon"><Plus /></el-icon>
        <h4 class="empty-title">暂无提供商</h4>
        <p class="empty-desc">添加你的第一个模型提供商以开始使用</p>
        <el-button type="primary" :icon="Plus" @click="openAddDialog">
          添加提供商
        </el-button>
      </div>

      <!-- 提供商列表 -->
      <div v-else class="provider-list">
        <div
          v-for="provider in providers"
          :key="provider.id"
          class="provider-card"
        >
          <div class="provider-card__top">
            <div class="provider-info">
              <div class="provider-name-row">
                <h4 class="provider-name">{{ provider.name }}</h4>
                <span
                  class="provider-status"
                  :class="provider.enabled ? 'is-active' : 'is-inactive'"
                >
                  {{ provider.enabled ? '启用' : '停用' }}
                </span>
              </div>
              <div class="provider-meta">
                <div class="meta-item">
                  <span class="meta-label">提供商</span>
                  <span class="meta-value">{{ provider.provider }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">API 地址</span>
                  <span class="meta-value">{{ provider.base_url }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">API Key</span>
                  <span class="meta-value mono">{{ maskApiKey(provider.api_key_masked) }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">默认模型</span>
                  <span class="meta-value">{{ provider.default_model }}</span>
                </div>
              </div>
            </div>
            <div class="provider-actions">
              <el-switch
                :model-value="provider.enabled"
                :loading="loading"
                size="small"
                @click="toggleEnabled(provider)"
              />
              <el-button
                size="small"
                circle
                :icon="Edit"
                @click="openEditDialog(provider)"
              />
              <el-button
                size="small"
                circle
                type="danger"
                :icon="Delete"
                @click="handleDelete(provider)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="520px"
      :close-on-click-modal="false"
      class="provider-dialog"
    >
      <el-form
        ref="dialogFormRef"
        class="dialog-form"
        label-position="top"
        :model="dialogForm"
        :rules="dialogRules"
      >
        <el-form-item label="提供商名称" prop="name">
          <el-input
            v-model="dialogForm.name"
            placeholder="例：我的 OpenAI 服务"
          />
        </el-form-item>

        <el-form-item label="提供商类型" prop="provider">
          <el-select
            v-model="dialogForm.provider"
            placeholder="请选择类型"
            style="width: 100%"
            @change="handleProviderChange"
          >
            <el-option
              v-for="opt in PROVIDER_OPTIONS"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="API 地址" prop="base_url">
          <el-input
            v-model="dialogForm.base_url"
            placeholder="https://api.openai.com"
          />
        </el-form-item>

        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="dialogForm.api_key"
            :placeholder="isEditing ? (editingMaskedKey || '输入新的 API Key（留空不修改）') : 'sk-...'"
            type="password"
            show-password
          />
        </el-form-item>

        <el-form-item label="默认模型" prop="default_model" v-if="!isEditing">
          <el-input
            v-model="dialogForm.default_model"
            placeholder="例：gpt-4o, claude-sonnet-4-6"
          />
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="dialogForm.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="handleDialogSubmit">
          {{ isEditing ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.settings-section {
  max-width: 640px;
}

.section-header {
  margin-bottom: 2rem;
}

.section-header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.section-title {
  margin: 0 0 0.5rem;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.section-desc {
  margin: 0;
  font-size: 0.88rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.section-body {
  padding: 0;
  min-height: 200px;
}

/* ── 空状态 ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1rem;
  text-align: center;
}

.empty-icon {
  color: var(--text-tertiary);
  margin-bottom: 1rem;
  opacity: 0.4;
}

.empty-title {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-desc {
  margin: 0 0 1.25rem;
  font-size: 0.85rem;
  color: var(--text-tertiary);
}

/* ── 提供商卡片 ── */
.provider-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.provider-card {
  padding: 1rem 0;
  border-bottom: 1px solid var(--line-soft);
  transition: all 0.15s ease;
}

.provider-card:last-child {
  border-bottom: none;
}

.provider-card__top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.provider-info {
  flex: 1;
  min-width: 0;
}

.provider-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 0.75rem;
}

.provider-name {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.provider-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.provider-status.is-active {
  background: rgba(74, 157, 154, 0.1);
  color: var(--success);
}

.provider-status.is-inactive {
  background: rgba(156, 163, 175, 0.1);
  color: var(--text-tertiary);
}

.provider-status::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.provider-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
}

.meta-label {
  color: var(--text-tertiary);
  flex-shrink: 0;
  min-width: 70px;
}

.meta-value {
  color: var(--text-secondary);
  word-break: break-all;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-value.mono {
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.78rem;
  letter-spacing: 0.02em;
}

.provider-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.provider-actions .el-button {
  --el-button-size: 32px;
}

/* ── 对话框 ── */
.dialog-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.88rem;
  padding-bottom: 0.25rem;
}

.dialog-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 0.25rem 0.75rem;
  background: var(--bg-page) !important;
  box-shadow: 0 0 0 1px var(--line-strong) inset;
  transition: all 0.2s ease;
}

.dialog-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(74, 157, 154, 0.3) inset;
}

.dialog-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--brand) inset;
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .section-body {
    padding: 0;
  }

  .section-header-row {
    flex-direction: column;
  }

  .provider-card__top {
    flex-direction: column;
  }

  .provider-actions {
    align-self: flex-end;
  }
}
</style>
