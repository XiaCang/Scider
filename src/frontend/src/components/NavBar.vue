<script setup lang="ts">
import {
  ArrowDown,
  Compass,
  Grid,
  Reading,
  Share,
  SwitchButton,
} from '@element-plus/icons-vue'
import type { Component } from 'vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLogo from './AppLogo.vue'
import { useAuthStore } from '../store/auth'

interface NavItem {
  label: string
  path: string
  icon: Component
  description: string
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navigationItems: NavItem[] = [
  { label: 'Dashboard', path: '/app/dashboard', icon: Grid, description: 'Overview' },
  { label: 'Library', path: '/app/library', icon: Reading, description: 'Paper collection' },
  { label: 'Knowledge Graph', path: '/app/graph', icon: Share, description: 'Concept map' },
  { label: 'Discover', path: '/app/discover', icon: Compass, description: 'Recommendations' },
]

const activePath = computed(() => {
  if (route.path.startsWith('/app/discover')) return '/app/discover'
  return route.path
})

const displayName = computed(() => authStore.displayName)

const handleNavigate = async (path: string) => {
  if (path !== route.path) {
    await router.push(path)
  }
}

const handleLogout = async () => {
  authStore.logout()
  await router.replace('/login')
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
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </button>
        </nav>
      </div>

      <el-dropdown trigger="click">
        <button class="workspace-user" type="button">
          <span class="workspace-user__avatar">
            {{ displayName.slice(0, 1).toUpperCase() }}
          </span>
          <el-icon><ArrowDown /></el-icon>
        </button>
        <template #dropdown>
          <el-dropdown-menu class="user-dropdown-menu">
            <div class="user-dropdown-header">
              <strong>{{ displayName }}</strong>
              <small>Personal Workspace</small>
            </div>
            <el-dropdown-item divided @click="handleLogout" class="logout-item">
              <el-icon><SwitchButton /></el-icon>
              <span>Sign out</span>
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
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
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
  gap: 0.5rem;
  height: 100%;
  align-items: center;
}

/* 基础导航项：圆角矩形 */
.header-nav__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;          /* 上下增加内边距，形成矩形 */
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: 0.5rem;         /* 圆角 */
  transition: all 0.2s ease;
  line-height: 1;
}

/* hover 状态：半透明品牌色背景 */
.header-nav__item:hover {
  color: var(--brand);
  background: color-mix(in srgb, var(--brand) 12%, transparent);
}

/* 激活状态：圆角矩形高亮 */
.header-nav__item.is-active {
  color: var(--brand);
  background: color-mix(in srgb, var(--brand) 15%, transparent);
  font-weight: 600;
}

/* 移除原有的下划线样式 */
/* .header-nav__item.is-active::after 已删除 */

.workspace-user {
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}

.workspace-user__avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--brand);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.user-dropdown-header {
  padding: 10px 16px;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid rgba(15, 23, 42, 0.05);
  margin-bottom: 5px;
}

.user-dropdown-header strong {
  font-size: 0.9rem;
  color: var(--text-primary);
}

.user-dropdown-header small {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.logout-item {
  color: #f56c6c !important;
}

.logout-item:hover {
  background-color: #fef0f0 !important;
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