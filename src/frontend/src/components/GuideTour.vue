<script setup lang="ts">
import { watch, nextTick, onBeforeUnmount, computed } from 'vue'
import { Close } from '@element-plus/icons-vue'
import type { TourStep } from '../hooks/useGuide'

const props = defineProps<{
  step: TourStep | null
  stepNumber: number
  totalSteps: number
  isFirst: boolean
  isLast: boolean
}>()

const emit = defineEmits<{
  next: []
  prev: []
  skip: []
}>()

/** 被高亮元素的锚点信息 */
const anchor = computed(() => {
  if (!props.step) return null
  try {
    const el = document.querySelector(props.step.selector) as HTMLElement | null
    if (!el) return null
    const rect = el.getBoundingClientRect()
    return {
      top: rect.top,
      left: rect.left,
      width: rect.width,
      height: rect.height,
    }
  } catch {
    return null
  }
})

const TOOLTIP_W = 320

/** 根据锚点和 placement 计算原始 tooltip 坐标 */
function calcRawPosition(
  a: NonNullable<ReturnType<typeof anchor.value>>,
  placement: string,
  gap: number,
) {
  let top: number, left: number, transform: string
  switch (placement) {
    case 'top':
      top = a.top - gap
      left = a.left + a.width / 2
      transform = 'translate(-50%, -100%)'
      break
    case 'bottom':
      top = a.top + a.height + gap
      left = a.left + a.width / 2
      transform = 'translate(-50%, 0)'
      break
    case 'left':
      top = a.top + a.height / 2
      left = a.left - gap
      transform = 'translate(-100%, -50%)'
      break
    case 'right':
      top = a.top + a.height / 2
      left = a.left + a.width + gap
      transform = 'translate(0, -50%)'
      break
    default:
      top = a.top + a.height + gap
      left = a.left + a.width / 2
      transform = 'translate(-50%, 0)'
  }
  return { top, left, transform }
}

/** 将 tooltip 约束在视口内 */
function clampToViewport(r: { top: number; left: number; transform: string }) {
  const vw = window.innerWidth
  const vh = window.innerHeight
  const margin = 12

  let { top, left } = r

  // 根据 transform 反推实际左上角坐标
  if (r.transform.includes('-50%, 0)')) {
    left = left - TOOLTIP_W / 2
  } else if (r.transform.includes('-50%, -100%')) {
    left = left - TOOLTIP_W / 2
    top = top - (TOOLTIP_W * 0.35) // 估计高度
  } else if (r.transform.includes('-100%, -50%')) {
    left = left - TOOLTIP_W
    top = top - (TOOLTIP_W * 0.35) / 2
  } else if (r.transform.includes('0, -50%')) {
    // left 不变
    top = top - (TOOLTIP_W * 0.35) / 2
  }

  // 边界裁剪
  if (left < margin) left = margin
  if (top < margin) top = margin
  if (left + TOOLTIP_W > vw - margin) left = vw - margin - TOOLTIP_W
  const estimatedHeight = TOOLTIP_W * 0.7
  if (top + estimatedHeight > vh - margin) top = vh - margin - estimatedHeight

  // 返回时把左上角坐标转回用于 position 的 left/top（不再用 transform 偏移）
  return {
    top: `${top}px`,
    left: `${left}px`,
    transform: 'none',
  }
}

/** 提示框位置计算 */
const tooltipStyle = computed(() => {
  const placement = props.step?.placement ?? 'bottom'
  const gap = 12

  if (anchor.value) {
    const raw = calcRawPosition(anchor.value, placement, gap)
    return clampToViewport(raw)
  }

  // 没有锚点时居中显示
  const vw = window.innerWidth
  const vh = window.innerHeight
  return {
    top: `${vh / 2 - 100}px`,
    left: `${(vw - TOOLTIP_W) / 2}px`,
    transform: 'none',
  }
})

/** 提示框箭头方向 */
const arrowClass = computed(() => `arrow-${props.step?.placement ?? 'bottom'}`)
</script>

<template>
  <Teleport to="body">
    <div v-if="step" class="guide-tour-overlay">
      <!-- 高亮边框（仅在目标元素存在时显示） -->
      <div
        v-if="anchor"
        class="guide-tour-highlight"
        :style="{
          top: `${anchor.top - 6}px`,
          left: `${anchor.left - 6}px`,
          width: `${anchor.width + 12}px`,
          height: `${anchor.height + 12}px`,
        }"
      />

      <!-- 提示卡片 -->
      <div
        class="guide-tour-tooltip"
        :class="arrowClass"
        :style="tooltipStyle"
      >
        <div class="guide-tour-tooltip__head">
          <span class="guide-tour-tooltip__step">
            {{ stepNumber }} / {{ totalSteps }}
          </span>
          <button class="guide-tour-tooltip__close" type="button" @click="emit('skip')">
            <el-icon><Close /></el-icon>
          </button>
        </div>
        <h3 class="guide-tour-tooltip__title">{{ step.title }}</h3>
        <p class="guide-tour-tooltip__desc">{{ step.description }}</p>
        <div class="guide-tour-tooltip__actions">
          <button
            v-if="!isFirst"
            class="guide-tour-btn guide-tour-btn--secondary"
            type="button"
            @click="emit('prev')"
          >
            上一步
          </button>
          <button
            v-if="!isLast"
            class="guide-tour-btn guide-tour-btn--primary"
            type="button"
            @click="emit('next')"
          >
            下一步
          </button>
          <button
            v-else
            class="guide-tour-btn guide-tour-btn--primary"
            type="button"
            @click="emit('skip')"
          >
            完成
          </button>
          <button
            class="guide-tour-btn guide-tour-btn--text"
            type="button"
            @click="emit('skip')"
          >
            跳过
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style>
.guide-tour-overlay {
  position: fixed;
  inset: 0;
  z-index: 99999;
  pointer-events: none;
}

.guide-tour-highlight {
  position: fixed;
  border-radius: 12px;
  box-shadow:
    0 0 0 4px rgba(74, 157, 154, 0.45),
    0 0 0 8px rgba(74, 157, 154, 0.15);
  pointer-events: none;
  z-index: 100001;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── 提示卡片 ── */
.guide-tour-tooltip {
  position: fixed;
  z-index: 100002;
  pointer-events: auto;
  background: #ffffff;
  border-radius: 14px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.18),
    0 0 0 1px rgba(0, 0, 0, 0.06);
  padding: 18px 20px 14px;
  width: 320px;
  max-width: calc(100vw - 32px);
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.guide-tour-tooltip__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.guide-tour-tooltip__step {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--brand, #4a9d9a);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.guide-tour-tooltip__close {
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  padding: 2px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s, background 0.15s;
}

.guide-tour-tooltip__close:hover {
  color: #374151;
  background: #f3f4f6;
}

.guide-tour-tooltip__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: #1f2937;
  letter-spacing: -0.01em;
  line-height: 1.35;
}

.guide-tour-tooltip__desc {
  margin: 8px 0 0;
  font-size: 0.84rem;
  color: #6b7280;
  line-height: 1.6;
}

.guide-tour-tooltip__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}

.guide-tour-btn {
  border: none;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  padding: 7px 16px;
  transition: all 0.15s ease;
}

.guide-tour-btn--primary {
  background: var(--brand, #4a9d9a);
  color: #fff;
}

.guide-tour-btn--primary:hover {
  background: #3d8b88;
}

.guide-tour-btn--secondary {
  background: #f3f4f6;
  color: #374151;
}

.guide-tour-btn--secondary:hover {
  background: #e5e7eb;
}

.guide-tour-btn--text {
  background: transparent;
  color: #9ca3af;
  padding: 7px 8px;
}

.guide-tour-btn--text:hover {
  color: #6b7280;
}
</style>
