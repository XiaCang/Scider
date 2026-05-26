<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { getProfileApi, updateProfileApi, uploadAvatarApi, getAvatarApi, deleteAvatarApi } from '../../../api/auth'
import { useAuthStore } from '../../../store/auth'
import type { ProfileResponseData } from '../../../types/auth'

const authStore = useAuthStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const uploading = ref(false)
const profile = ref<ProfileResponseData | null>(null)
const initialLoading = ref(true)

const form = reactive({
  username: '',
  bio: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 30, message: '用户名长度应为 2-30 位', trigger: 'blur' },
  ],
}

const avatarUrl = ref<string | null>(null)
const fileInput = ref<HTMLInputElement>()

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

/** 将后端返回的相对路径拼成完整 URL
 * 后端在 /api 下提供 API，但静态文件挂载在 /uploads/ 下，
 * 所以需要从 API_BASE 中提取 origin（协议+主机）来拼接 */
const resolveAvatarUrl = (path: string | null): string | null => {
  if (!path) return null
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  try {
    const origin = new URL(API_BASE).origin
    return `${origin}${path}`
  } catch {
    return API_BASE ? `${API_BASE.replace(/\/+$/, '')}${path}` : path
  }
}

const fetchProfile = async () => {
  initialLoading.value = true
  try {
    const [profileRes, avatarRes] = await Promise.all([
      getProfileApi(),
      getAvatarApi().catch(() => null),
    ])
    profile.value = profileRes.data
    form.username = profileRes.data.user.name
    if (avatarRes?.data?.avatarUrl) {
      avatarUrl.value = resolveAvatarUrl(avatarRes.data.avatarUrl)
    }
  } catch (error) {
    ElMessage.error('获取用户信息失败')
  } finally {
    initialLoading.value = false
  }
}

const handleAvatarChange = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  // 预览
  const reader = new FileReader()
  reader.onload = (ev) => {
    avatarUrl.value = ev.target?.result as string
  }
  reader.readAsDataURL(file)

  uploading.value = true
  try {
    const res = await uploadAvatarApi(file)
    if (res.data?.avatarUrl) {
      avatarUrl.value = resolveAvatarUrl(res.data.avatarUrl)
    }
    ElMessage.success('头像已更新')
  } catch (error) {
    // 上传失败，回退到之前的头像
    ElMessage.error(error instanceof Error ? error.message : '头像上传失败')
    await fetchProfile()
  } finally {
    uploading.value = false
  }

  // 清空 input 以便重复选择同一文件
  target.value = ''
}

const handleDeleteAvatar = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除当前头像吗？',
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      }
    )
    await deleteAvatarApi()
    avatarUrl.value = null
    ElMessage.success('头像已删除')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error instanceof Error ? error.message : '删除失败')
    }
  }
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await updateProfileApi({ username: form.username, bio: form.bio })
      // 更新 store 中的用户名
      if (authStore.user) {
        authStore.user.username = form.username
      }
      ElMessage.success('个人资料已更新')
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '更新失败')
    } finally {
      loading.value = false
    }
  })
}

onMounted(() => {
  fetchProfile()
})
</script>

<template>
  <div class="settings-section">
    <div class="section-header">
      <h3 class="section-title">个人资料</h3>
      <p class="section-desc">修改你的头像和用户名</p>
    </div>

    <div class="section-body" v-loading="initialLoading">
      <!-- 头像 -->
      <div class="avatar-section">
        <div class="avatar-label">头像</div>
        <div class="avatar-row">
          <div class="avatar-preview" @click="triggerFileInput">
            <template v-if="avatarUrl">
              <img :src="avatarUrl" alt="avatar" class="avatar-img" />
            </template>
            <template v-else>
              <span class="avatar-initial">
                {{ profile?.user.name?.slice(0, 1).toUpperCase() || '?' }}
              </span>
            </template>
            <div class="avatar-overlay">
              <el-icon :size="20"><Plus /></el-icon>
            </div>
          </div>
          <div class="avatar-info">
            <div class="avatar-actions">
              <button class="upload-btn" @click="triggerFileInput">
                {{ uploading ? '上传中...' : '更换头像' }}
              </button>
              <button
                v-if="avatarUrl"
                class="delete-btn"
                @click="handleDeleteAvatar"
              >
                <el-icon :size="14"><Delete /></el-icon>
                删除
              </button>
            </div>
            <p class="avatar-hint">支持 JPG、PNG、WebP 格式</p>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept="image/png,image/jpeg,image/jpg,image/webp"
            class="file-input-hidden"
            @change="handleAvatarChange"
          />
        </div>
      </div>

      <el-divider />

      <!-- 表单 -->
      <el-form
        ref="formRef"
        class="settings-form"
        label-position="top"
        :model="form"
        :rules="rules"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="邮箱">
          <el-input :model-value="profile?.user.email" disabled placeholder="邮箱不可修改">
            <template #append>
              <span class="email-badge">已验证</span>
            </template>
          </el-input>
        </el-form-item>

        <div class="form-actions">
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            保存修改
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.settings-section {
  max-width: 560px;
}

.section-header {
  margin-bottom: 2rem;
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
}

/* ── 头像 ── */
.avatar-section {
  margin-bottom: 0.5rem;
}

.avatar-label {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.avatar-preview {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  background: var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-initial {
  font-size: 1.6rem;
  font-weight: 700;
  color: #fff;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
  color: #fff;
}

.avatar-preview:hover .avatar-overlay {
  opacity: 1;
}

.avatar-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.avatar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-btn {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  background: var(--bg-page);
  color: var(--text-primary);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.upload-btn:hover {
  border-color: var(--brand);
  color: var(--brand);
  background: rgba(74, 157, 154, 0.06);
}

.delete-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  background: var(--bg-page);
  color: var(--danger);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.delete-btn:hover {
  border-color: var(--danger);
  background: rgba(245, 108, 108, 0.06);
}

.avatar-hint {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-tertiary);
}

.file-input-hidden {
  display: none;
}

/* ── 邮箱标签 ── */
.email-badge {
  font-size: 0.78rem;
  color: var(--success);
  font-weight: 500;
}

/* ── 表单 ── */
.settings-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.88rem;
  padding-bottom: 0.25rem;
}

.settings-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 0.25rem 0.75rem;
  background: var(--bg-page) !important;
  box-shadow: 0 0 0 1px var(--line-strong) inset;
  transition: all 0.2s ease;
}

.settings-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(74, 157, 154, 0.3) inset;
}

.settings-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--brand) inset;
}

/* 禁用输入框样式 */
.settings-form :deep(.el-input.is-disabled .el-input__wrapper) {
  background: var(--bg-muted) !important;
}

.settings-form :deep(.el-input-group__append) {
  background: transparent;
  border: none;
  padding-left: 0;
}

.form-actions {
  margin-top: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--line-soft);
}

.form-actions .el-button {
  min-width: 140px;
  min-height: 38px;
  font-size: 0.9rem;
  font-weight: 600;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.form-actions .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(74, 157, 154, 0.2);
}

@media (max-width: 768px) {
  .section-body {
    padding: 0;
  }

  .avatar-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
