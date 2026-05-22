<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import { changePasswordByOldApi } from '../../../api/auth'

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const rules: FormRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应为 6-20 位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await changePasswordByOldApi({
        old_password: form.old_password,
        new_password: form.new_password,
      })
      ElMessage.success('密码修改成功')
      formRef.value!.resetFields()
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '密码修改失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <div class="settings-section">
    <div class="section-header">
      <h3 class="section-title">重置密码</h3>
      <p class="section-desc">请先输入当前密码，再设置新密码</p>
    </div>

    <div class="section-body">
      <el-form
        ref="formRef"
        class="settings-form"
        label-position="top"
        :model="form"
        :rules="rules"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="当前密码" prop="old_password">
          <el-input
            v-model="form.old_password"
            type="password"
            show-password
            placeholder="请输入当前密码"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="form.new_password"
            type="password"
            show-password
            placeholder="请输入新密码（6-20位）"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input
            v-model="form.confirm_password"
            type="password"
            show-password
            placeholder="再次输入新密码"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <div class="form-actions">
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            确认修改
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.settings-section {
  max-width: 520px;
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
}
</style>
