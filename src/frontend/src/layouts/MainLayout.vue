<script setup lang="ts">
import NavBar from '../components/NavBar.vue'

</script>

<template>
  <div class="workspace-shell">

    <NavBar />

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
  flex-direction: column;
  min-height: 100vh;
  background: #fbfcfe;
}

/* 二级工具栏样式保留（即使注释，预留样式） */
.workspace-sub-header {
  background: white;
  border-bottom: 1px solid rgba(15, 23, 42, 0.05);
  height: 48px;
}

.discover-tabs {
  display: flex;
  margin-left: 9px;
  margin-top: 10px;
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
  width: 100%;
  margin: 0 auto;
  padding: 0rem;
  box-sizing: border-box;
}

/* 响应式调整（仅保留与内容相关的部分） */
@media (max-width: 768px) {
  .workspace-content {
    padding: 1rem;
  }
}
</style>