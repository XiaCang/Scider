<script setup lang="ts">
import { Lock, Message, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import AppLogo from '../../components/AppLogo.vue'
import NetworkBackdrop from '../../components/NetworkBackdrop.vue'
import { sendCodeApi, changePasswordApi } from '../../api/auth'

const router = useRouter()

const formRef = ref<FormInstance>()
const loading = ref(false)
const codeSending = ref(false)
const countdown = ref(0)
const stepDone = ref(false) // true = 密码重置成功

const form = reactive({
  email: '',
  code: '',
  password: '',
  password2: '',
})

// 倒计时
let timer: number | null = null

const startCountdown = (seconds: number) => {
  if (timer) clearInterval(timer)
  countdown.value = seconds
  timer = window.setInterval(() => {
    if (countdown.value <= 1) {
      if (timer) clearInterval(timer)
      timer = null
      countdown.value = 0
    } else {
      countdown.value--
    }
  }, 1000)
}

const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'change'] },
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码应为 6 位', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应为 6-20 位', trigger: 'blur' },
  ],
  password2: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const sendCode = async () => {
  if (!formRef.value) return
  await formRef.value.validateField('email', (valid) => {
    if (!valid) return
  })

  codeSending.value = true
  try {
    const res = await sendCodeApi({ email: form.email })
    if (res.data?.sent) {
      ElMessage.success('验证码已发送至邮箱，请查收')
    } else {
      ElMessage.warning('验证码已生成（未配置 SMTP，仅在服务端日志可查）')
    }
    startCountdown(60)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '发送验证码失败')
  } finally {
    codeSending.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await changePasswordApi({
        email: form.email,
        code: form.code,
        new_password: form.password,
      })
      ElMessage.success('密码重置成功，请重新登录')
      stepDone.value = true
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '重置密码失败')
    } finally {
      loading.value = false
    }
  })
}

const goLogin = () => {
  router.replace('/login')
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-page__mesh auth-page__mesh--left">
      <NetworkBackdrop />
    </div>
    <div class="auth-page__mesh auth-page__mesh--right">
      <NetworkBackdrop />
    </div>

    <section class="auth-panel panel-surface">
      <div class="auth-panel__header">
        <AppLogo size="56" />
      </div>

      <!-- 重置成功 -->
      <template v-if="stepDone">
        <div class="success-state">
          <div class="success-icon">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              <circle cx="32" cy="32" r="30" stroke="#4a9d9a" stroke-width="4" fill="rgba(74,157,154,0.08)" />
              <path d="M20 33l8 8 16-16" stroke="#4a9d9a" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </div>
          <h3 class="success-title">密码已重置</h3>
          <p class="success-desc">请使用新密码重新登录</p>
          <button class="success-btn" @click="goLogin">前往登录</button>
        </div>
      </template>

      <!-- 表单 -->
      <template v-else>
        <div class="auth-panel__copy">
          <h2>忘记密码</h2>
          <p>输入注册邮箱，通过验证码重置密码</p>
        </div>

        <el-form
          ref="formRef"
          class="auth-form"
          label-position="top"
          :model="form"
          :rules="rules"
          @submit.prevent="handleSubmit"
        >
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="请输入注册邮箱">
              <template #prefix>
                <el-icon><Message /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="验证码" prop="code">
            <div class="captcha-wrapper">
              <el-input v-model="form.code" placeholder="请输入6位验证码">
                <template #prefix>
                  <el-icon><Message /></el-icon>
                </template>
              </el-input>
              <el-button
                :disabled="countdown > 0 || codeSending"
                @click="sendCode"
                type="primary"
                plain
              >
                {{ countdown > 0 ? `${countdown}s 后重试` : '获取验证码' }}
              </el-button>
            </div>
          </el-form-item>

          <el-form-item label="新密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入新密码（6-20位）">
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="确认密码" prop="password2">
            <el-input v-model="form.password2" type="password" show-password placeholder="再次输入新密码">
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-button class="auth-form__submit" type="primary" :loading="loading" @click="handleSubmit">
            重置密码
          </el-button>
        </el-form>

        <div class="auth-footer">
          <button class="back-link" @click="goLogin">
            <el-icon><ArrowLeft /></el-icon>
            返回登录
          </button>
        </div>
      </template>
    </section>
  </div>
</template>

<style scoped>
/* ── 页面容器 ── */
.auth-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: #faf8f5;
}

.auth-page__mesh {
  position: absolute;
  opacity: 0.6;
  pointer-events: none;
}

.auth-page__mesh--left {
  left: -10%;
  top: 20%;
  width: min(50vw, 600px);
}

.auth-page__mesh--right {
  right: -10%;
  bottom: 15%;
  width: min(48vw, 560px);
  transform: scaleX(-1);
}

/* ── 主面板 ── */
.auth-panel {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 440px;
  padding: 2.5rem;
  border-radius: 16px;
  background: #ffffff;
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.04),
    0 0 0 1px rgba(0, 0, 0, 0.04);
}

.auth-panel__header {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

/* ── 标题 ── */
.auth-panel__copy {
  text-align: center;
  margin-bottom: 2rem;
}

.auth-panel__copy h2 {
  margin: 0 0 0.5rem;
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: #1f2937;
}

.auth-panel__copy p {
  margin: 0;
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.6;
}

/* ── 验证码 ── */
.captcha-wrapper {
  display: flex;
  gap: 12px;
  align-items: center;
}

.captcha-wrapper .el-button {
  flex-shrink: 0;
  white-space: nowrap;
}

/* ── 表单 ── */
.auth-form {
  width: 100%;
}

.auth-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #1f2937;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.auth-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 0.75rem 1rem;
  background: #faf8f5 !important;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.08) inset;
  transition: all 0.2s ease;
}

.auth-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(74, 157, 154, 0.3) inset;
}

.auth-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #4a9d9a inset;
}

.auth-form :deep(.el-input__inner) {
  font-size: 0.95rem;
}

.auth-form__submit {
  width: 100%;
  margin-top: 1.5rem;
  min-height: 3.2rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 10px;
  letter-spacing: 0.02em;
  transition: all 0.2s ease;
}

.auth-form__submit:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(74, 157, 154, 0.25);
}

/* ── 底部链接 ── */
.auth-footer {
  text-align: center;
  margin-top: 1.5rem;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 0.88rem;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.back-link:hover {
  color: #4a9d9a;
}

/* ── 重置成功状态 ── */
.success-state {
  text-align: center;
  padding: 1rem 0;
}

.success-icon {
  margin-bottom: 1.25rem;
}

.success-title {
  margin: 0 0 0.5rem;
  font-size: 1.35rem;
  font-weight: 600;
  color: #1f2937;
}

.success-desc {
  margin: 0 0 1.5rem;
  color: #6b7280;
  font-size: 0.9rem;
}

.success-btn {
  display: inline-flex;
  align-items: center;
  padding: 0.7rem 2rem;
  border: none;
  border-radius: 10px;
  background: #4a9d9a;
  color: white;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(74, 157, 154, 0.25);
}

.success-btn:hover {
  background: #3d8b88;
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(74, 157, 154, 0.3);
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .auth-page {
    padding: 1.5rem;
  }

  .auth-panel {
    padding: 2rem 1.5rem;
    max-width: 100%;
  }

  .auth-panel__copy h2 {
    font-size: 1.3rem;
  }

  .captcha-wrapper {
    flex-direction: column;
    align-items: stretch;
  }

  .captcha-wrapper .el-button {
    margin-left: 0;
    width: 100%;
  }
}

@media (max-width: 480px) {
  .auth-page {
    padding: 1rem;
  }

  .auth-panel {
    padding: 1.5rem 1.2rem;
    border-radius: 14px;
  }
}
</style>
