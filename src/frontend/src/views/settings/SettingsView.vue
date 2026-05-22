<script setup lang="ts">
import { ref } from 'vue'
import { Lock, User, Connection } from '@element-plus/icons-vue'
import ResetPasswordSection from './sections/ResetPasswordSection.vue'
import ProfileSection from './sections/ProfileSection.vue'
import ModelProvidersSection from './sections/ModelProvidersSection.vue'

type TabKey = 'password' | 'profile' | 'providers'

interface SidebarItem {
  key: TabKey
  label: string
  icon: object
}

const sidebarItems: SidebarItem[] = [
  { key: 'password', label: '重置密码', icon: Lock },
  { key: 'profile', label: '个人资料', icon: User },
  { key: 'providers', label: '模型提供商', icon: Connection },
]

const activeTab = ref<TabKey>('password')
</script>

<template>
  <div class="settings-page">
    <div class="settings-layout">
      <!-- 左侧导航 -->
      <aside class="settings-sidebar">
        <div class="settings-sidebar__header">
          <h2 class="settings-sidebar__title">设置</h2>
        </div>
        <nav class="settings-sidebar__nav">
          <button
            v-for="item in sidebarItems"
            :key="item.key"
            class="settings-nav-item"
            :class="{ 'is-active': activeTab === item.key }"
            @click="activeTab = item.key"
          >
            <el-icon :size="18">
              <component :is="item.icon" />
            </el-icon>
            <span>{{ item.label }}</span>
          </button>
        </nav>
      </aside>

      <!-- 右侧内容 -->
      <main class="settings-content">
        <transition name="fade-slide" mode="out-in">
          <ResetPasswordSection v-if="activeTab === 'password'" key="password" />
          <ProfileSection v-else-if="activeTab === 'profile'" key="profile" />
          <ModelProvidersSection v-else-if="activeTab === 'providers'" key="providers" />
        </transition>
      </main>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  min-height: calc(100vh - 64px);
  background: var(--bg-page);
}

.settings-layout {
  display: flex;
  max-width: 1000px;
  margin: 0 auto;
  min-height: calc(100vh - 64px);
}

/* ── 左侧导航 ── */
.settings-sidebar {
  width: 220px;
  flex-shrink: 0;
  padding: 2rem 1rem 2rem 0;
  position: sticky;
  top: 64px;
  height: calc(100vh - 64px);
  overflow-y: auto;
}

.settings-sidebar__header {
  padding: 0 0 1.25rem 1rem;
  border-bottom: 1px solid var(--line-soft);
  margin-bottom: 0.75rem;
}

.settings-sidebar__title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.settings-sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.settings-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  border: none;
  background: transparent;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
}

.settings-nav-item:hover {
  background: rgba(74, 157, 154, 0.06);
  color: var(--text-primary);
}

.settings-nav-item.is-active {
  background: rgba(74, 157, 154, 0.1);
  color: var(--brand);
  font-weight: 600;
}

.settings-nav-item.is-active .el-icon {
  color: var(--brand);
}

.settings-nav-item .el-icon {
  flex-shrink: 0;
  color: var(--text-tertiary);
  transition: color 0.15s ease;
}

.settings-nav-item:hover .el-icon {
  color: var(--text-secondary);
}

/* ── 右侧内容区 ── */
.settings-content {
  flex: 1;
  padding: 2rem 0 2rem 2rem;
  border-left: 1px solid var(--line-soft);
  min-height: calc(100vh - 64px);
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .settings-layout {
    flex-direction: column;
  }

  .settings-sidebar {
    width: 100%;
    position: static;
    height: auto;
    padding: 1rem;
    border-bottom: 1px solid var(--line-soft);
  }

  .settings-sidebar__nav {
    flex-direction: row;
    overflow-x: auto;
    gap: 4px;
  }

  .settings-nav-item {
    white-space: nowrap;
    flex-shrink: 0;
  }

  .settings-content {
    padding: 1.5rem 1rem;
    border-left: none;
  }
}
</style>
