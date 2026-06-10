<script setup lang="ts">
import { Lock, Message, User } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { reactive, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppLogo from '../../components/AppLogo.vue'
import NetworkBackdrop from '../../components/NetworkBackdrop.vue'
import { useAuthStore } from '../../store/auth'
import { sendCodeApi } from '../../api/auth'  // 根据你的实际路径调整

type AuthMode = 'login' | 'register'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 表单 ref
const formRef = ref<FormInstance>()

const mode = ref<AuthMode>('login')
const loading = ref(false)
const codeSending = ref(false)
const countdown = ref(0)

const form = reactive({
  name: '',
  email: '',
  password: '',
  code: ''
})

// 表单校验规则
const rules = computed<FormRules>(() => {
  const baseRules: FormRules = {
    email: [
      { required: true, message: '请输入邮箱', trigger: 'blur' },
      { type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'change'] }
    ],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 6, max: 20, message: '密码长度应为 6-20 位', trigger: 'blur' }
    ]
  }

  if (mode.value === 'register') {
    baseRules.name = [
      { required: true, message: '请输入昵称', trigger: 'blur' },
      { min: 2, max: 20, message: '昵称长度应为 2-20 个字符', trigger: 'blur' }
    ]
    baseRules.code = [
      { required: true, message: '请输入验证码', trigger: 'blur' },
      { len: 6, message: '验证码应为 6 位数字', trigger: 'blur' } // 假设验证码6位
    ]
  }

  return baseRules
})

// 倒计时定时器句柄
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

const sendCode = async () => {
  // 先校验邮箱
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

const switchMode = (nextMode: AuthMode) => {
  mode.value = nextMode
  // 切换模式时清空验证码和倒计时，并重置表单校验状态
  form.code = ''
  if (timer) clearInterval(timer)
  countdown.value = 0
  formRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      if (mode.value === 'login') {
        await authStore.login({
          email: form.email,
          password: form.password
        })
        ElMessage.success('登录成功')
      } else {
        await authStore.register({
          name: form.name,
          email: form.email,
          password: form.password,
          code: form.code
        })
        ElMessage.success('账号创建成功')
      }

      const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/app/library'
      await router.replace(redirect)
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '认证失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <div class="auth-page">
    <!-- 背景网格 -->
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

      <div class="auth-switcher-wrapper">
        <div class="auth-switcher">
          <button
            class="auth-switcher__item"
            :class="{ 'is-active': mode === 'login' }"
            type="button"
            @click="switchMode('login')"
          >
            登录
          </button>
          <button
            class="auth-switcher__item"
            :class="{ 'is-active': mode === 'register' }"
            type="button"
            @click="switchMode('register')"
          >
            注册
          </button>
        </div>
      </div>

      <el-form
        ref="formRef"
        class="auth-form"
        label-position="top"
        :model="form"
        :rules="rules"
        @submit.prevent="handleSubmit"
      >
        <!-- 注册时显示姓名 -->
        <el-form-item v-if="mode === 'register'" label="昵称" prop="name">
          <el-input v-model="form.name" placeholder="请输入昵称">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <!-- 邮箱 -->
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱地址">
            <template #prefix>
              <el-icon><Message /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <!-- 密码 -->
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码">
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
          <!-- 忘记密码链接（仅登录模式） -->
          <div v-if="mode === 'login'" class="forgot-link-wrapper">
            <button type="button" class="forgot-link" @click="router.push('/forgot-password')">
              忘记密码？
            </button>
          </div>
        </el-form-item>

        <!-- 注册时显示验证码 -->
        <el-form-item v-if="mode === 'register'" label="验证码" prop="code">
          <div class="captcha-wrapper">
            <el-input v-model="form.code" placeholder="请输入验证码">
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

        <el-button class="auth-form__submit" type="primary" :loading="loading" @click="handleSubmit">
          {{ mode === 'login' ? '登录' : '注册' }}
        </el-button>
      </el-form>
    </section>
  </div>
</template>

<style scoped>
/* 验证码布局 */
.captcha-wrapper {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 忘记密码链接 */
.forgot-link-wrapper {
  text-align: right;
  margin-top: 4px;
}

.forgot-link {
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 0.82rem;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.forgot-link:hover {
  color: #4a9d9a;
}

.captcha-wrapper .el-button {
  flex-shrink: 0;
  white-space: nowrap;
}

/* 页面容器 */
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

/* 背景装饰 */
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

/* 主面板 */
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

/* Logo区域 */
.auth-panel__header {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

/* 切换器包装器 */
.auth-switcher-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
}

.auth-switcher {
  display: inline-flex;
  padding: 0.3rem;
  border-radius: 999px;
  background: #f5f0ea;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.04);
}

.auth-switcher__item {
  border: 0;
  background: transparent;
  padding: 0.6rem 1.8rem;
  border-radius: 999px;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
  white-space: nowrap;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.auth-switcher__item:hover {
  color: #4a9d9a;
}

.auth-switcher__item.is-active {
  background: white;
  color: #4a9d9a;
  box-shadow:
    0 4px 12px rgba(74, 157, 154, 0.15),
    0 2px 4px rgba(0, 0, 0, 0.06);
  font-weight: 600;
}

/* 标题和描述 */
.auth-panel__copy {
  text-align: center;
  margin-bottom: 2rem;
}

.auth-panel__copy h2 {
  margin: 0 0 0.5rem;
  font-size: 1.75rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}

.auth-panel__copy p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.95rem;
  line-height: 1.6;
}

/* 表单样式 */
.auth-form {
  width: 100%;
}

.auth-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.auth-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 0.75rem 1rem;
  box-shadow: 0 0 0 1px var(--line-soft) inset;
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

/* 提交按钮 */
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

/* 响应式设计 */
@media (max-width: 768px) {
  .auth-page {
    padding: 1.5rem;
  }

  .auth-panel {
    padding: 2rem 1.5rem;
    max-width: 100%;
  }

  .auth-panel__copy h2 {
    font-size: 1.5rem;
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
    border-radius: 20px;
  }

  .auth-switcher__item {
    padding: 0.5rem 1.4rem;
    font-size: 0.9rem;
  }
}
</style>