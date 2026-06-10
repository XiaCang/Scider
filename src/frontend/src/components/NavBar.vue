<script setup lang="ts">
import { ArrowDown, SwitchButton, Setting } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLogo from './AppLogo.vue'
import { useAuthStore } from '../store/auth'

interface NavItem {
  label: string
  path: string
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navigationItems: NavItem[] = [
  { label: '我的文库', path: '/app/library' },
  { label: '知识图谱', path: '/app/graph' },
  { label: '发现论文', path: '/app/discover' },
  { label: '上下游', path: '/app/discover-upstream' },
]

const activePath = computed(() => {
  if (route.path.startsWith('/app/library')) return '/app/library'
  return route.path
})

const displayName = computed(() => authStore.displayName)
const userAvatarUrl = computed(() => authStore.avatarUrl)
const hasAvatar = computed(() => Boolean(userAvatarUrl.value))

const handleNavigate = async (path: string) => {
  if (path !== route.path) {
    await router.push(path)
  }
}

const handleLogout = async () => {
  authStore.logout()
  await router.replace('/login')
}

const handleSettings = async () => {
  await router.push('/app/settings')
}
</script>

<template>
  <header class="workspace-header">
    <div class="header-container">
      <div class="header-left">
        <div class="header-brand">
          <AppLogo size="36" />
        </div>
        <nav class="header-nav">
          <button
            v-for="item in navigationItems"
            :key="item.path"
            class="header-nav__item"
            :class="{ 'is-active': activePath === item.path }"
            type="button"
            @click="handleNavigate(item.path)"
          >
            <span>{{ item.label }}</span>
          </button>
        </nav>
      </div>

      <el-dropdown trigger="click" popper-class="user-dropdown-popper" placement="bottom-end">
        <button class="workspace-user" type="button">
          <span class="workspace-user__avatar">
            <img
              v-if="hasAvatar"
              :src="userAvatarUrl!"
              :alt="displayName"
              class="workspace-user__avatar-img"
            />
            <template v-else>
              {{ displayName.slice(0, 1).toUpperCase() }}
            </template>
          </span>
          <el-icon><ArrowDown /></el-icon>
        </button>
        <template #dropdown>
          <el-dropdown-menu class="user-dropdown-menu">
            <div class="user-dropdown-header">
              <strong>{{ displayName }}</strong>
            </div>
            <el-dropdown-item @click="handleSettings">
              <el-icon><Setting /></el-icon>
              <span>设置</span>
            </el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout" class="logout-item">
              <el-icon><SwitchButton /></el-icon>
              <span>登出</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<style scoped>
.workspace-header {
  height: 64px;
  background: rgba(250, 248, 245, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-container {
  width: 100%;
  max-width: none;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  box-sizing: border-box;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 2.5rem;
  height: 100%;
}

.header-brand {
  flex-shrink: 0;
}

.header-nav {
  display: flex;
  gap: 0.25rem;
  height: 100%;
  align-items: center;
}

/* 基础导航项 */
.header-nav__item {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: 0.9rem;
  transition: all 0.2s ease;
  line-height: 1;
}

/* hover 状态 */
.header-nav__item:hover {
  color: #4a9d9a;
  background: rgba(74, 157, 154, 0.08);
}

/* 激活状态 */
.header-nav__item.is-active {
  color: #4a9d9a;
  background: rgba(74, 157, 154, 0.12);
  font-weight: 600;
}

/* 移除原有的下划线样式 */
/* .header-nav__item.is-active::after 已删除 */

.workspace-user {
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  outline: none;
}

.workspace-user__avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #4a9d9a;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.9rem;
  overflow: hidden;
}

.workspace-user__avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.user-dropdown-header {
  padding: 10px 14px 8px;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid #f3f4f6;
  margin-bottom: 2px;
}

.user-dropdown-header strong {
  font-size: 0.88rem;
  font-weight: 600;
  color: #1f2937;
  letter-spacing: -0.01em;
}

.user-dropdown-header small {
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

/* ── 退出按钮 ── */
.logout-item {
  color: #c17767 !important;
}

.logout-item .el-icon {
  color: #c17767 !important;
}

.logout-item:not(.is-disabled):hover {
  background: #faf8f5 !important;
  color: #b16a5a !important;
}

.logout-item:not(.is-disabled):hover .el-icon {
  color: #b16a5a !important;
}

/* 响应式 */
@media (max-width: 768px) {
  .header-nav {
    display: none;
  }
  .header-container {
    padding: 0 1rem;
  }
}
</style>

<style>
/* ── 非 scoped，专门覆盖 teleported 的下拉菜单 ── */
.user-dropdown-popper {
  border: 1px solid #f3f4f6 !important;
  border-radius: 12px !important;
  padding: 4px !important;
  min-width: 160px !important;
  background: #ffffff !important;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.1) !important;
}

.user-dropdown-popper .el-dropdown-menu__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  color: #1f2937 !important;
  transition: all 0.15s ease;
  margin: 1px 0;
}

.user-dropdown-popper .el-dropdown-menu__item .el-icon {
  font-size: 1rem;
  color: #9ca3af;
  transition: color 0.15s ease;
}

/* 👇 这里是真正解决 hover 蓝色的地方 */
.user-dropdown-popper .el-dropdown-menu__item:not(.is-disabled):hover {
  background: #faf8f5 !important;
  color: #1f2937 !important;
}

.user-dropdown-popper .el-dropdown-menu__item:not(.is-disabled):hover .el-icon {
  color: #6b7280 !important;
}

/* 分隔线 */
.user-dropdown-popper .el-dropdown-menu__item.is-divided {
  margin-top: 4px;
  border-top: 1px solid #f3f4f6;
}

/* 退出按钮 */
.user-dropdown-popper .logout-item {
  color: #c17767 !important;
}

.user-dropdown-popper .logout-item .el-icon {
  color: #c17767 !important;
}

.user-dropdown-popper .logout-item:not(.is-disabled):hover {
  background: #faf8f5 !important;
  color: #b16a5a !important;
}

.user-dropdown-popper .logout-item:not(.is-disabled):hover .el-icon {
  color: #b16a5a !important;
}
</style>