<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getProfileApi } from '../../api/auth'
import type { ProfileResponseData } from '../../types/auth'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const profile = ref<ProfileResponseData | null>(null)

const fetchProfile = async () => {
  loading.value = true
  try {
    const response = await getProfileApi()
    profile.value = response.data
  } catch (error) {
    ElMessage.error('获取用户信息失败')
    console.error('Failed to fetch profile:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchProfile()
})
</script>

<template>
  <div class="profile-container">
    <el-card class="profile-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">个人信息</span>
        </div>
      </template>

      <div v-if="profile" class="profile-content">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="用户名">
            {{ profile.user.name }}
          </el-descriptions-item>
          <el-descriptions-item label="邮箱">
            {{ profile.user.email }}
          </el-descriptions-item>
          <el-descriptions-item label="用户ID">
            {{ profile.user.id }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.profile-container {
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
}

.profile-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.profile-content {
  padding: 1rem 0;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  color: var(--text-secondary);
  width: 120px;
}

:deep(.el-descriptions__content) {
  color: var(--text-primary);
}

@media (max-width: 768px) {
  .profile-container {
    padding: 1rem;
  }

  :deep(.el-descriptions__label) {
    width: 100px;
  }
}
</style>
