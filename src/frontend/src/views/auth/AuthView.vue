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
      { required: true, message: '请输入姓名', trigger: 'blur' },
      { min: 2, max: 20, message: '姓名长度应为 2-20 个字符', trigger: 'blur' }
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
    await sendCodeApi({ email: form.email })
    ElMessage.success('验证码已发送至邮箱，请查收')
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
        ElMessage.success('Login successful.')
      } else {
        await authStore.register({
          name: form.name,
          email: form.email,
          password: form.password,
          code: form.code
        })
        ElMessage.success('Account created successfully.')
      }

      const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/app/dashboard'
      await router.replace(redirect)
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : 'Authentication failed.')
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <div class="auth-page">
    <!-- 背景网格（保持不变） -->
    <div class="auth-page__mesh auth-page__mesh--left">
      <NetworkBackdrop />
    </div>
    <div class="auth-page__mesh auth-page__mesh--right">
      <NetworkBackdrop />
    </div>

    <div class="auth-shell page-shell">
      <section class="auth-intro">
        <AppLogo size="48"/>
        <h1 style="font-size: 32px;">把分散的论文阅读，整理成一张能持续生长的个人知识网络。</h1>
        <p>
          Scider 面向科研新手，帮助你完成上传、提炼、关联和推荐的完整阅读闭环，减少“读后即忘”和文献追踪成本。
        </p>

        <ul class="auth-intro__points">
          <li>上传 PDF 后自动生成 Key Points 提炼任务</li>
          <li>围绕关键词和主题构建知识图谱入口</li>
          <li>基于研究方向提供 arXiv 推荐与上下游检索框架</li>
        </ul>
      </section>

      <section class="auth-panel panel-surface">
        <div class="auth-panel__header">
          <AppLogo />
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

        <div class="auth-panel__copy">
          <h2>{{ mode === 'login' ? 'Sign in to Scider' : 'Create your Scider workspace' }}</h2>
          <p>
            {{ mode === 'login'
              ? '使用邮箱进入你的论文工作台。'
              : '先用基础信息完成注册，后续可直接对接后端真实接口。' }}
          </p>
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
          <el-form-item v-if="mode === 'register'" label="姓名" prop="name">
            <el-input v-model="form.name" placeholder="例如：张同学">
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <!-- 邮箱（登录/注册均需要） -->
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="Enter your academic email">
              <template #prefix>
                <el-icon><Message /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <!-- 密码 -->
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="Password">
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <!-- 注册时显示验证码 + 发送按钮 -->
          <el-form-item v-if="mode === 'register'" label="验证码" prop="code">
            <div class="captcha-wrapper">
              <el-input v-model="form.code" placeholder="请输入验证码" style="flex: 1;">
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

          <!-- 登录时不再显示 remember me 选项（已移除） -->

          <el-button class="auth-form__submit" type="primary" :loading="loading" @click="handleSubmit">
            {{ mode === 'login' ? 'Sign In' : 'Create Account' }}
          </el-button>
        </el-form>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* 原有样式保持不变，仅补充验证码布局 */
.captcha-wrapper {
  display: flex;
  gap: 12px;
  align-items: center;
}

.captcha-wrapper .el-button {
  flex-shrink: 0;
  white-space: nowrap;
}

/* 以下是你原有的样式，请完整保留 */
.auth-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.auth-page__mesh {
  position: absolute;
  opacity: 0.78;
  pointer-events: none;
}

.auth-page__mesh--left {
  left: -6%;
  top: 16%;
  width: min(44vw, 580px);
}

.auth-page__mesh--right {
  right: -8%;
  bottom: 10%;
  width: min(42vw, 520px);
  transform: scaleX(-1);
}

.auth-shell {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(380px, 480px);
  align-items: center;
  gap: 2rem;
}

.auth-intro {
  position: relative;
  z-index: 1;
  padding: 2rem 1rem 2rem 0;
}

.auth-intro h1 {
  margin: 1.3rem 0 1rem;
  font-size: clamp(2.4rem, 5vw, 4.4rem);
  line-height: 1.04;
  letter-spacing: -0.05em;
}

.auth-intro p {
  max-width: 34rem;
  color: var(--text-secondary);
  font-size: 1.02rem;
  line-height: 1.8;
}

.auth-intro__points {
  margin: 2rem 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.82rem;
}

.auth-intro__points li {
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
  color: var(--text-secondary);
}

.auth-intro__points li::before {
  content: '';
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  background: var(--brand-accent);
  box-shadow: 0 0 0 6px rgba(47, 107, 255, 0.09);
}

.auth-panel {
  position: relative;
  z-index: 1;
  padding: 1.5rem;
  border-radius: 28px;
}

.auth-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.auth-switcher {
  display: inline-flex;
  padding: 0.25rem;
  border-radius: 999px;
  background: var(--bg-muted);
  flex-shrink: 0;
}

.auth-switcher__item {
  border: 0;
  background: transparent;
  padding: 0.5rem 1.2rem;
  border-radius: 999px;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.auth-switcher__item.is-active {
  background: white;
  color: var(--brand);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
}

.auth-panel__copy {
  margin: 2rem 0 1.1rem;
}

.auth-panel__copy h2 {
  margin: 0;
  font-size: 2rem;
  letter-spacing: -0.03em;
}

.auth-panel__copy p {
  margin: 0.65rem 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

/* 已删除 .auth-form__meta 相关样式，因为 remember me 被移除 */

.auth-form__submit {
  width: 100%;
  margin-top: 1rem;
  min-height: 3rem;
}

@media (max-width: 1080px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }

  .auth-intro {
    padding-right: 0;
  }
}

@media (max-width: 720px) {
  .auth-page {
    padding: 0.9rem;
  }

  .auth-panel {
    padding: 1.1rem;
  }

  .auth-panel__header {
    flex-direction: column;
    align-items: flex-start;
  }

  .auth-switcher {
    width: 100%;
  }

  .auth-switcher__item {
    flex: 1;
  }

  .captcha-wrapper {
    flex-direction: column;
    align-items: stretch;
  }

  .captcha-wrapper .el-button {
    margin-left: 0;
  }
}
</style>