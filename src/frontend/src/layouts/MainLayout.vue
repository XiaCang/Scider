<script setup lang="ts">
import {
  ArrowDown,
  Compass,
  Connection,
  Grid,
  Menu,
  Plus,
  Reading,
  Search,
  Share,
  SwitchButton,
  Upload,
} from '@element-plus/icons-vue'
import type { Component } from 'vue'
import { computed, ref } from 'vue'
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

const sidebarOpen = ref(false)
const quickSearch = ref('')

const navigationItems: NavItem[] = [
  { label: 'Dashboard', path: '/app/dashboard', icon: Grid, description: 'Overview' },
  { label: 'Library', path: '/app/library', icon: Reading, description: 'Paper collection' },
  { label: 'Knowledge Graph', path: '/app/graph', icon: Share, description: 'Concept map' },
  { label: 'Discover', path: '/app/discover', icon: Compass, description: 'Recommendations' },
]

const activePath = computed(() => route.path)
const displayName = computed(() => authStore.displayName)

// 判断是否在 Discover 模块
const isDiscoverModule = computed(() => {
  return route.path.startsWith('/app/discover')
})

// Discover 模块的当前子页面
const discoverActiveTab = computed(() => {
  if (route.name === 'discover-upstream') {
    return 'upstream'
  }
  return 'keyword'
})

const handleNavigate = async (path: string) => {
  sidebarOpen.value = false
  if (path !== route.path) {
    await router.push(path)
  }
}

const handleLogout = async () => {
  authStore.logout()
  await router.replace('/login')
}

const handleUpload = () => {
  window.alert('Upload entry is ready. Connect this button to your PDF upload dialog later.')
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
    <aside class="workspace-sidebar" :class="{ 'is-open': sidebarOpen }">
      <div class="workspace-sidebar__brand">
        <AppLogo />
      </div>

      <nav class="workspace-nav">
        <button
          v-for="item in navigationItems"
          :key="item.path"
          class="workspace-nav__item"
          :class="{ 'is-active': activePath === item.path }"
          type="button"
          @click="handleNavigate(item.path)"
        >
          <el-icon class="workspace-nav__icon">
            <component :is="item.icon" />
          </el-icon>
          <span>
            <strong>{{ item.label }}</strong>
            <small>{{ item.description }}</small>
          </span>
        </button>
      </nav>

      <div class="workspace-sidebar__footer">
        <div class="workspace-sidebar__tip">
          <p>Hello</p>
        </div>
      </div>
    </aside>

    <div class="workspace-main">
      <header class="workspace-topbar">
        <div class="workspace-topbar__left">
          <el-button class="workspace-topbar__menu" circle plain @click="sidebarOpen = !sidebarOpen">
            <el-icon><Menu /></el-icon>
          </el-button>

          <!-- 非 Discover 模块显示标题 -->
          <div v-if="!isDiscoverModule" class="workspace-topbar__title">
            <h1 v-if="route.name === 'dashboard'" class="topbar-title">Dashboard</h1>
            <h1 v-else-if="route.name === 'library'" class="topbar-title">My Library</h1>
            <h1 v-else-if="route.name === 'graph'" class="topbar-title">Knowledge Graph</h1>
          </div>

          <!-- Discover 模块增加切换按钮 -->
          <div v-else class="discover-tabs">
            <h1 class="topbar-title">Discover</h1>

            <button
              class="discover-tab"
              :class="{ 'is-active': discoverActiveTab === 'keyword' }"
              type="button"
              @click="handleDiscoverTabChange('keyword')"
            >
              <el-icon><Search /></el-icon>
              <span>关键词检索</span>
            </button>
            <button
              class="discover-tab"
              :class="{ 'is-active': discoverActiveTab === 'upstream' }"
              type="button"
              @click="handleDiscoverTabChange('upstream')"
            >
              <el-icon><Connection /></el-icon>
              <span>上下游检索</span>
            </button>
          </div>
        </div>

        <div class="workspace-topbar__actions">
          <el-button plain @click="handleUpload">
            <el-icon><Upload /></el-icon>
            Upload Paper
          </el-button>
          <el-dropdown>
            <button class="workspace-user" type="button">
              <span class="workspace-user__avatar">{{ displayName.slice(0, 1).toUpperCase() }}</span>
              <span class="workspace-user__meta">
                <strong>{{ displayName }}</strong>
                <small>Research Workspace</small>
              </span>
              <el-icon><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleNavigate('/app/dashboard')">Dashboard</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  Sign out
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="workspace-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
.workspace-shell {
  display: flex;
  width: 100%;
  min-height: 100vh;
  background: #fbfcfe;
}

.workspace-shell::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at top left, rgba(216, 227, 255, 0.35), transparent 26%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.85) 0%, rgba(248, 250, 253, 0.94) 100%);
  z-index: 0;
}

.workspace-shell > * {
  position: relative;
  z-index: 1;
}

.workspace-sidebar {
  width: var(--sidebar-width);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 1.2rem 0.9rem;
  background: rgba(255, 255, 255, 0.88);
  border-right: 1px solid rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(16px);
}

.workspace-sidebar__brand p,
.workspace-sidebar__tip p {
  margin: 0.7rem 0 0;
  color: var(--text-secondary);
  font-size: 0.84rem;
  line-height: 1.6;
}

.workspace-nav {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-top: 1.5rem;
}

.workspace-nav__item {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  width: 100%;
  border: 0;
  background: transparent;
  border-radius: 10px;
  padding: 0.68rem 0.75rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition:
    background 0.2s ease,
    transform 0.2s ease;
}

.workspace-nav__item:hover {
  background: rgba(22, 50, 95, 0.045);
}

.workspace-nav__item.is-active {
  background: var(--brand-soft);
  color: var(--brand);
}

.workspace-nav__item span {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.workspace-nav__item strong {
  font-size: 0.88rem;
}

.workspace-nav__item small {
  color: var(--text-tertiary);
  font-size: 0.72rem;
}

.workspace-nav__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.8rem;
  height: 1.8rem;
  border-radius: 8px;
  background: rgba(22, 50, 95, 0.05);
}

.workspace-sidebar__footer {
  margin-top: auto;
}

.workspace-sidebar__tip {
  padding: 1rem 0.25rem 0;
  border-top: 1px solid rgba(15, 23, 42, 0.08);
}

.workspace-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 100vh;
}

.workspace-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-height: 60px;
  padding: 0 1.4rem;
  background: rgba(255, 255, 255, 0.72);
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(12px);
}

.workspace-topbar__left,
.workspace-topbar__actions {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.workspace-topbar__menu {
  display: none;
}

.discover-tabs {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.topbar-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.discover-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid var(--line-soft);
  background: white;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  font-size: 0.88rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.discover-tab:hover {
  background: rgba(22, 50, 95, 0.045);
}

.discover-tab.is-active {
  background: var(--brand-soft);
  color: var(--brand);
  border-color: var(--brand);
}

.workspace-user {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  border: 0;
  background: transparent;
  cursor: pointer;
  padding: 0.2rem;
}

.workspace-user__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: linear-gradient(180deg, #173668 0%, #102648 100%);
  color: white;
  font-weight: 700;
}

.workspace-user__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.workspace-user__meta small {
  color: var(--text-tertiary);
  font-size: 0.72rem;
}

.workspace-content {
  flex: 1;
  padding: 1.2rem 1.5rem 1.5rem;
  min-width: 0;
}

@media (max-width: 1100px) {
  .workspace-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 20;
    width: min(320px, calc(100vw - 1rem));
    transform: translateX(-100%);
    transition: transform 0.24s ease;
    box-shadow: 0 20px 50px rgba(15, 23, 42, 0.14);
  }

  .workspace-sidebar.is-open {
    transform: translateX(0);
  }

  .workspace-topbar__menu {
    display: inline-flex;
  }
}

@media (max-width: 820px) {
  .workspace-topbar {
    flex-direction: column;
    align-items: stretch;
    min-height: auto;
    padding: 0.9rem 1rem;
  }

  .workspace-topbar__left,
  .workspace-topbar__actions {
    width: 100%;
  }

  .workspace-topbar__actions {
    justify-content: space-between;
    flex-wrap: wrap;
  }

  .workspace-user__meta {
    display: none;
  }

  .workspace-content {
    padding: 1rem;
  }
}
</style>


