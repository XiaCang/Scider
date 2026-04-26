<script setup lang="ts">
import {
  ArrowDown,
  Compass,
  Connection,
  Grid,
  Reading,
  Search,
  Share,
  SwitchButton,
  Upload,
} from '@element-plus/icons-vue'
import type { Component } from 'vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppLogo from '../components/AppLogo.vue'
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
  // 匹配基础路径，确保 Discover 的子页面也能激活主导航
  if (route.path.startsWith('/app/discover')) return '/app/discover'
  return route.path
})

const displayName = computed(() => authStore.displayName)

const isDiscoverModule = computed(() => route.path.startsWith('/app/discover'))

const discoverActiveTab = computed(() => {
  return route.name === 'discover-upstream' ? 'upstream' : 'keyword'
})

const handleNavigate = async (path: string) => {
  if (path !== route.path) {
    await router.push(path)
  }
}

const handleLogout = async () => {
  authStore.logout()
  await router.replace('/login')
}

const handleUpload = () => {
  window.alert('Upload entry is ready.')
}

const handleDiscoverTabChange = (tab: string) => {
  if (tab === 'keyword' && route.name !== 'discover') {
    router.push('/app/discover')
  } else if (tab === 'upstream' && route.name !== 'discover-upstream') {
    router.push('/app/discover-upstream')
  }
}
</script>

<template>
  <div class="workspace-shell">
    <header class="workspace-header">
      <div class="header-container">
        <div class="header-left">
          <div class="header-brand">
            <AppLogo size="36"/>
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
            <span class="workspace-user__avatar">{{ displayName.slice(0, 1).toUpperCase() }}</span>
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

    <section v-if="isDiscoverModule || route.name !== 'dashboard'" class="workspace-sub-header">
      <div class="header-container">
        <div v-if="isDiscoverModule" class="discover-tabs">
          <button
            class="discover-tab"
            :class="{ 'is-active': discoverActiveTab === 'keyword' }"
            @click="handleDiscoverTabChange('keyword')"
          >
            <el-icon><Search /></el-icon>
            <span>关键词检索</span>
          </button>
          <button
            class="discover-tab"
            :class="{ 'is-active': discoverActiveTab === 'upstream' }"
            @click="handleDiscoverTabChange('upstream')"
          >
            <el-icon><Connection /></el-icon>
            <span>上下游检索</span>
          </button>
        </div>
        <div v-else class="page-title-area">
          <h1 class="page-title">{{ route.name === 'library' ? 'My Library' : 'Knowledge Graph' }}</h1>
        </div>
      </div>
    </section>

    <main class="workspace-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.workspace-shell {
  display: flex;
  flex-direction: column; /* 纵向排列 */
  min-height: 100vh;
  background: #fbfcfe;
}

/* 顶部主导航栏 */
.workspace-header {
  height: 64px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  position: sticky;
  top: 0;
  z-index: 1000;
}

/* 左侧包装容器：让 Logo 和 Nav 靠左并排 */
.header-left {
  display: flex;
  align-items: center;
  gap: 2.5rem;            /* Logo 和 导航菜单之间的间距 */
  height: 100%;
}

/* 导航菜单样式微调 */
.header-nav {
  display: flex;
  gap: 0.5rem;
  height: 100%;
}

/* 右侧操作区：保持原有靠右逻辑 */
.header-actions {
  display: flex;
  align-items: center;
  gap: 1.2rem;
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

.header-brand {
  flex-shrink: 0;
}

.header-nav__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0 1rem;
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.header-nav__item:hover {
  color: var(--brand);
}

.header-nav__item.is-active {
  color: var(--brand);
}

.header-nav__item.is-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 15%;
  right: 15%;
  height: 3px;
  background: var(--brand);
  border-radius: 3px 3px 0 0;
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

.user-info-tip {
  padding: 0.8rem 1rem;
  min-width: 160px;
}
.user-info-tip strong { display: block; font-size: 0.9rem; }
.user-info-tip p { font-size: 0.75rem; color: var(--text-tertiary); margin: 4px 0 0; }

/* 二级工具栏 */
.workspace-sub-header {
  background: white;
  border-bottom: 1px solid rgba(15, 23, 42, 0.05);
  height: 48px;
}

.page-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.discover-tabs {
  display: flex;
  gap: 1.5rem;
  height: 100%;
}

.discover-tab {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  border: 0;
  background: transparent;
  font-size: 0.85rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0 0.5rem;
  transition: color 0.2s;
}

.discover-tab.is-active {
  color: var(--brand);
  font-weight: 600;
}

/* 内容区域 */
.workspace-content {
  flex: 1;
  max-width: 1440px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem;
  box-sizing: border-box;
}


/* 下拉菜单容器样式 */
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

/* 退出登录按钮样式 */
.logout-item {
  color: #f56c6c !important; /* 危险红 */
}

.logout-item:hover {
  background-color: #fef0f0 !important;
}

/* 修正原生按钮的默认边框（如果是作为 dropdown 触发器） */
.workspace-user {
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .header-nav { display: none; } /* 移动端可改为抽屉，这里简单隐藏 */
  .upload-btn span { display: none; }
  .header-container { gap: 1rem; }
}
</style>