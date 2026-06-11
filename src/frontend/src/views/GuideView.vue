<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { RefreshRight } from '@element-plus/icons-vue'
import GuideContent from '../components/GuideContent.vue'
import { resetAllTours } from '../hooks/useGuide'

function resetGuide(): void {
  resetAllTours()
  ElMessage.success('所有页面引导已重置，刷新或重新进入页面后将再次展示引导')
}
</script>

<template>
  <div class="guide-page">
    <div class="guide-page__inner">
      <GuideContent />

      <!-- 重置引导区域 -->
      <div class="guide-reset">
        <div class="guide-reset__card">
          <p class="guide-reset__text">
            错过了首次引导？点击下方按钮重置引导状态，下次打开页面时将重新展示功能导览。
          </p>
          <el-button
            type="primary"
            plain
            size="default"
            :icon="RefreshRight"
            @click="resetGuide"
          >
            重新查看引导
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.guide-page {
  min-height: calc(100vh - 64px);
  background: var(--bg-page, #faf8f5);
}

.guide-page__inner {
  padding: 24px 0;
}

/* ── 重置引导区域 ── */
.guide-reset {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 16px 40px;
}

.guide-reset__card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  background: var(--bg-solid, #fff);
  border: 1px solid var(--line-soft, rgba(0, 0, 0, 0.06));
  border-radius: 14px;
  padding: 20px 24px;
}

.guide-reset__text {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
  flex: 1;
}

@media (max-width: 768px) {
  .guide-reset__card {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
