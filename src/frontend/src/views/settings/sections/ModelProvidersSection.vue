<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete, Edit, ArrowLeft, Connection } from '@element-plus/icons-vue'
import { getProvidersApi, createProviderApi, updateProviderApi, deleteProviderApi } from '../../../api/settings'
import type { ModelProvider, CreateProviderPayload, ModelItem } from '../../../types/settings'

// ── 预置数据 ──
const PROVIDER_OPTIONS = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Google', value: 'google' },
  { label: 'Azure', value: 'azure' },
  { label: '自定义', value: 'custom' },
]

const PROVIDER_META: Record<string, { label: string; color: string; icon: string }> = {
  openai: { label: 'OpenAI', color: '#10a37f', icon: 'O' },
  anthropic: { label: 'Anthropic', color: '#d97757', icon: 'A' },
  google: { label: 'Google', color: '#4285f4', icon: 'G' },
  azure: { label: 'Azure', color: '#0078d4', icon: 'Z' },
  custom: { label: '自定义', color: '#6b7280', icon: 'C' },
}

const PROVIDER_BASE_URLS: Record<string, string> = {
  openai: 'https://api.openai.com',
  anthropic: 'https://api.anthropic.com',
  google: 'https://generativelanguage.googleapis.com',
  azure: '',
  custom: '',
}

/** 各提供商已知的常用模型列表（后端接口不可用时的降级方案） */
const FALLBACK_MODELS: Record<string, ModelItem[]> = {
  openai: [
    { id: 'gpt-4o', name: 'GPT-4o' },
    { id: 'gpt-4o-mini', name: 'GPT-4o mini' },
    { id: 'o3-mini', name: 'O3 mini' },
    { id: 'o1', name: 'O1' },
    { id: 'o1-mini', name: 'O1 mini' },
  ],
  anthropic: [
    { id: 'claude-opus-4-7', name: 'Claude Opus 4.7' },
    { id: 'claude-sonnet-4-6', name: 'Claude Sonnet 4.6' },
    { id: 'claude-sonnet-4', name: 'Claude Sonnet 4' },
    { id: 'claude-haiku-4-5', name: 'Claude Haiku 4.5' },
  ],
  google: [
    { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash' },
    { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro' },
    { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro' },
    { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash' },
  ],
}

// ── 状态 ──
const loading = ref(true)
const providers = ref<ModelProvider[]>([])
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const editingMaskedKey = ref('')
const dialogLoading = ref(false)
const dialogFormRef = ref<FormInstance>()

const currentStep = ref(1) // 1: 基本信息, 2: 选择模型

const dialogForm = reactive({
  name: '',
  provider: 'openai',
  base_url: '',
  api_key: '',
  default_model: '',
  enabled: true,
})

const availableModels = ref<ModelItem[]>([])
const modelsLoading = ref(false)
const modelsFetched = ref(false)
const modelsFetchError = ref('')

// ── 计算属性 ──
const isEditing = computed(() => editingId.value !== null)
const dialogTitle = computed(() => (isEditing.value ? '编辑提供商' : '添加提供商'))

const providerMeta = computed(() => PROVIDER_META[dialogForm.provider] || PROVIDER_META.custom)

const dialogRules: FormRules = {
  name: [{ required: true, message: '请输入提供商名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商类型', trigger: 'change' }],
  api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入 API 地址', trigger: 'blur' }],
}

// ── 方法 ──

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
  // 重置模型选择状态
  currentStep.value = 1
  modelsFetched.value = false
  availableModels.value = []
  modelsFetchError.value = ''
  dialogForm.default_model = ''
}

const openAddDialog = () => {
  editingId.value = null
  editingMaskedKey.value = ''
  currentStep.value = 1
  modelsFetched.value = false
  availableModels.value = []
  modelsFetchError.value = ''
  dialogForm.name = ''
  dialogForm.provider = 'openai'
  dialogForm.base_url = PROVIDER_BASE_URLS['openai']
  dialogForm.api_key = ''
  dialogForm.default_model = ''
  dialogForm.enabled = true
  dialogVisible.value = true
}

const openEditDialog = (provider: ModelProvider) => {
  editingId.value = provider.id
  editingMaskedKey.value = provider.api_key_masked
  currentStep.value = 1
  dialogForm.name = provider.name
  dialogForm.provider = provider.provider
  dialogForm.base_url = provider.base_url
  dialogForm.api_key = ''
  dialogForm.default_model = provider.default_model
  dialogForm.enabled = provider.enabled
  dialogVisible.value = true
}

/** 获取可用模型列表 — 直接通过 base_url/models 获取 */
const fetchAvailableModels = async () => {
  modelsLoading.value = true
  modelsFetchError.value = ''
  availableModels.value = []
  dialogForm.default_model = ''

  const baseUrl = dialogForm.base_url.replace(/\/+$/, '')
  const apiKey = dialogForm.api_key

  try {
    // 针对不同提供商构造不同的模型列表请求
    let modelsUrl = ''
    let headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (dialogForm.provider === 'anthropic') {
      modelsUrl = `${baseUrl}/v1/models`
      headers['x-api-key'] = apiKey
      headers['anthropic-version'] = '2023-06-01'
    } else if (dialogForm.provider === 'google') {
      modelsUrl = `${baseUrl}/v1beta/models?key=${apiKey}`
    } else {
      // OpenAI 兼容
      modelsUrl = `${baseUrl}/models`
      headers['Authorization'] = `Bearer ${apiKey}`
    }

    const res = await fetch(modelsUrl, { headers })
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`)
    }

    const json = await res.json()

    // 解析不同提供商的响应格式
    if (dialogForm.provider === 'anthropic') {
      availableModels.value = (json.data || [])
        .filter((m: any) => m.type === 'model')
        .map((m: any) => ({ id: m.id, name: m.display_name || m.id }))
    } else {
      // OpenAI 兼容格式: { data: [{ id, object: "model" }, ...] }
      availableModels.value = (json.data || [])
        .filter((m: any) => m.object === 'model' || !m.object)
        .map((m: any) => ({ id: m.id, name: m.id }))
    }

    if (availableModels.value.length === 0) {
      throw new Error('模型列表为空')
    }
  } catch {
    // 直接请求失败，回退到前端预置列表
    const fallback = FALLBACK_MODELS[dialogForm.provider]
    if (fallback) {
      availableModels.value = fallback
      modelsFetchError.value = '无法从服务端获取模型列表，已加载预置列表'
    } else {
      modelsFetchError.value = '无法获取模型列表，请检查 API 地址和 Key 是否正确'
    }
  } finally {
    modelsLoading.value = false
    modelsFetched.value = true
  }
}

const goToStep2 = async () => {
  if (!dialogFormRef.value) return
  await dialogFormRef.value.validate(async (valid) => {
    if (!valid) return
    modelsFetched.value = false
    currentStep.value = 2
    await fetchAvailableModels()
  })
}

const goBackToStep1 = () => {
  currentStep.value = 1
}

const handleDialogSubmit = async () => {
  // Step 2 (新增): 只校验模型选择，跳过表单校验
  if (currentStep.value === 2) {
    if (!dialogForm.default_model) {
      ElMessage.warning('请选择默认模型')
      return
    }
    return doSubmit()
  }

  // Step 1 或编辑模式: 先校验表单再提交
  if (!dialogFormRef.value) return
  try {
    await dialogFormRef.value.validate()
  } catch {
    return
  }
  await doSubmit()
}

async function doSubmit() {
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
      },
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
  if (key.length <= 8) return key.slice(0, 4) + '••••'
  return key.slice(0, 4) + '••••' + key.slice(-4)
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
        <el-icon :size="48" class="empty-icon"><Connection /></el-icon>
        <h4 class="empty-title">暂无提供商</h4>
        <p class="empty-desc">添加你的第一个模型提供商以开始使用</p>
        <el-button type="primary" :icon="Plus" @click="openAddDialog">
          添加提供商
        </el-button>
      </div>

      <!-- 提供商卡片 -->
      <div v-else class="provider-list">
        <div
          v-for="provider in providers"
          :key="provider.id"
          class="provider-card"
        >
          <div class="card-header">
            <div
              class="card-icon"
              :style="{ background: (PROVIDER_META[provider.provider] || PROVIDER_META.custom).color }"
            >
              {{ (PROVIDER_META[provider.provider] || PROVIDER_META.custom).icon }}
            </div>
            <div class="card-info">
              <div class="card-title-row">
                <h4 class="card-title">{{ provider.name }}</h4>
                <span
                  class="card-status"
                  :class="provider.enabled ? 'is-active' : 'is-inactive'"
                >
                  {{ provider.enabled ? '已启用' : '已停用' }}
                </span>
              </div>
            </div>
            <div class="card-actions">
              <el-switch
                :model-value="provider.enabled"
                size="small"
                @click="toggleEnabled(provider)"
              />
              <el-button size="small" circle :icon="Edit" @click="openEditDialog(provider)" />
              <el-button
                size="small"
                circle
                type="danger"
                :icon="Delete"
                @click="handleDelete(provider)"
              />
            </div>
          </div>
          <div class="card-body">
            <div class="meta-grid">
              <div class="meta-item">
                <span class="meta-label">提供商</span>
                <span class="meta-value">{{ (PROVIDER_META[provider.provider] || PROVIDER_META.custom).label }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">API 地址</span>
                <span class="meta-value mono">{{ provider.base_url }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">API Key</span>
                <span class="meta-value mono">{{ maskApiKey(provider.api_key_masked) }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">默认模型</span>
                <span class="meta-value model-tag">{{ provider.default_model }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="540px"
      :close-on-click-modal="false"
      class="provider-dialog"
      :before-close="() => { currentStep = 1; modelsFetched = false; availableModels = []; }"
    >
      <el-form
        ref="dialogFormRef"
        class="dialog-form"
        label-position="top"
        :model="dialogForm"
        :rules="dialogRules"
        v-show="currentStep === 1"
      >
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

        <el-form-item label="提供商名称" prop="name">
          <el-input v-model="dialogForm.name" placeholder="例：我的 OpenAI 服务" />
        </el-form-item>

        <el-form-item label="API 地址" prop="base_url">
          <el-input v-model="dialogForm.base_url" placeholder="https://api.openai.com" />
        </el-form-item>

        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="dialogForm.api_key"
            :placeholder="isEditing ? (editingMaskedKey || '输入新的 API Key（留空不修改）') : 'sk-...'"
            type="password"
            show-password
          />
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="dialogForm.enabled" />
        </el-form-item>
      </el-form>

      <!-- 步骤 2：选择模型 -->
      <div v-show="currentStep === 2" class="step-model-selection">
          <div class="step-header">
            <button class="back-btn" type="button" @click="goBackToStep1">
              <el-icon><ArrowLeft /></el-icon>
              返回修改
            </button>
            <p class="step-desc">选择该提供商使用的默认模型</p>
          </div>

          <div v-if="modelsLoading" class="models-loading">
            <el-skeleton :rows="4" animated />
          </div>

          <div v-else-if="modelsFetchError && availableModels.length === 0" class="models-error">
            <p>{{ modelsFetchError }}</p>
            <el-button size="small" @click="fetchAvailableModels">重试</el-button>
          </div>

          <div v-else class="models-list">
            <div class="model-option" v-for="model in availableModels" :key="model.id">
              <label class="model-option-label" :class="{ 'is-selected': dialogForm.default_model === model.id }">
                <el-radio
                  v-model="dialogForm.default_model"
                  :value="model.id"
                  size="large"
                >
                  <div class="model-option-content">
                    <span class="model-name">{{ model.name }}</span>
                    <span class="model-id">{{ model.id }}</span>
                  </div>
                </el-radio>
              </label>
            </div>

            <div v-if="availableModels.length === 0" class="models-empty">
              <p>暂无可用模型</p>
            </div>
          </div>
        </div>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>

        <template v-if="currentStep === 1">
          <el-button
            v-if="!isEditing"
            type="primary"
            :disabled="!dialogForm.api_key || !dialogForm.base_url"
            @click="goToStep2"
          >
            下一步 — 选择模型
          </el-button>
          <el-button
            v-else
            type="primary"
            :loading="dialogLoading"
            @click="handleDialogSubmit"
          >
            保存
          </el-button>
        </template>

        <template v-if="currentStep === 2">
          <el-button type="primary" :loading="dialogLoading" @click="handleDialogSubmit">
            添加
          </el-button>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.settings-section {
  max-width: 680px;
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
  padding: 3rem 1rem;
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

/* ── 提供商卡片列表 ── */
.provider-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.provider-card {
  background: var(--bg-solid);
  border-radius: 14px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--line-soft);
  overflow: hidden;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.provider-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
  transform: translateY(-1px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px 14px;
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  color: #fff;
  flex-shrink: 0;
}

.card-info {
  flex: 1;
  min-width: 0;
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.card-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.card-status.is-active {
  background: var(--brand-soft);
  color: var(--brand-accent);
}

.card-status.is-inactive {
  background: rgba(156, 163, 175, 0.1);
  color: var(--text-tertiary);
}

.card-status::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.card-actions .el-button {
  --el-button-size: 30px;
}

.card-body {
  padding: 0 20px 16px;
}

.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 16px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.meta-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.meta-value {
  font-size: 0.82rem;
  color: var(--text-secondary);
  word-break: break-all;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-value.mono {
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.76rem;
}

.meta-value.model-tag {
  display: inline-block;
  background: var(--brand-soft);
  color: var(--brand);
  padding: 1px 8px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 0.8rem;
  width: fit-content;
}

@media (max-width: 640px) {
  .meta-grid {
    grid-template-columns: 1fr;
  }
  .card-header {
    flex-wrap: wrap;
  }
}

/* ── 对话框样式 ── */
.dialog-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.88rem;
  padding-bottom: 0.25rem;
}

.dialog-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 0.25rem 0.75rem;
  background: var(--bg-muted) !important;
  box-shadow: 0 0 0 1px var(--line-strong) inset;
  transition: all 0.2s ease;
}

.dialog-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(74, 157, 154, 0.3) inset;
}

.dialog-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--brand) inset;
}

/* ── Select 下拉（非蓝色） ── */
.provider-dialog :deep(.el-select .el-select__wrapper) {
  background: var(--bg-muted) !important;
  box-shadow: 0 0 0 1px var(--line-strong) inset;
  border-radius: 10px;
}

.provider-dialog :deep(.el-select .el-select__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--brand) inset;
}

.provider-dialog :deep(.el-select-dropdown__item.selected) {
  color: var(--brand);
  font-weight: 600;
}

.provider-dialog :deep(.el-select-dropdown__item.hover) {
  background: var(--brand-soft);
}

/* ── Switch（非蓝色） ── */
.provider-dialog :deep(.el-switch.is-checked) {
  --el-switch-on-color: var(--brand);
}

/* ── Radio（非蓝色） ── */
.provider-dialog :deep(.el-radio__input.is-checked .el-radio__inner) {
  border-color: var(--brand);
  background: var(--brand);
}

.provider-dialog :deep(.el-radio__input.is-checked + .el-radio__label) {
  color: var(--brand);
}

.provider-dialog :deep(.el-radio__inner:hover) {
  border-color: var(--brand);
}

/* ── 步骤 2：选择模型 ── */
.step-model-selection {
  min-height: 200px;
}

.step-header {
  margin-bottom: 1rem;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-sm);
  background: var(--bg-solid);
  color: var(--text-secondary);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: 12px;
}

.back-btn:hover {
  border-color: #d1d5db;
  color: var(--text-primary);
  background: var(--bg-muted);
}

.step-desc {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.models-loading {
  padding: 1rem 0;
}

.models-error {
  text-align: center;
  padding: 2rem 1rem;
  color: var(--danger);
  font-size: 0.85rem;
}

.models-error .el-button {
  margin-top: 8px;
}

.models-empty {
  text-align: center;
  padding: 2rem;
  color: var(--text-tertiary);
  font-size: 0.85rem;
}

.models-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 320px;
  overflow-y: auto;
  padding: 2px;
}

.model-option-label {
  display: block;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: all 0.15s ease;
  background: var(--bg-page);
}

.model-option-label:hover {
  border-color: var(--brand);
  background: var(--brand-soft);
}

.model-option-label.is-selected {
  border-color: var(--brand);
  background: rgba(74, 157, 154, 0.06);
}

.model-option-label :deep(.el-radio) {
  display: flex;
  align-items: center;
  width: 100%;
  margin-right: 0;
}

.model-option-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-left: 8px;
}

.model-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.model-id {
  font-size: 0.78rem;
  color: var(--text-tertiary);
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .section-body {
    padding: 0;
  }

  .section-header-row {
    flex-direction: column;
  }
}
</style>

<style>
/* dialog footer 被 teleport 到 body 下，scoped 样式无效，故用全局样式覆写 */
.provider-dialog .el-button--primary {
  --el-button-bg-color: #4a9d9a;
  --el-button-border-color: #4a9d9a;
  --el-button-hover-bg-color: #3d8b88;
  --el-button-hover-border-color: #3d8b88;
  --el-button-active-bg-color: #357a77;
  --el-button-active-border-color: #357a77;
}
</style>
