import { ref, computed, onMounted } from 'vue'

export interface TourStep {
  /** CSS 选择器，用于定位页面元素 */
  selector: string
  /** 步骤标题 */
  title: string
  /** 步骤说明 */
  description: string
  /** 提示框相对于目标元素的位置 */
  placement?: 'top' | 'bottom' | 'left' | 'right'
}

export interface TourConfig {
  /** 页面唯一标识，用于 localStorage 记录 */
  pageKey: string
  /** 引导步骤列表 */
  steps: TourStep[]
}

const STORAGE_PREFIX = 'scider_tour_'

export function useGuide(config: TourConfig) {
  const currentStep = ref(-1)
  const isActive = computed(() => currentStep.value >= 0)
  const isFirst = computed(() => currentStep.value === 0)
  const isLast = computed(() => currentStep.value === config.steps.length - 1)
  const currentStepData = computed(() =>
    currentStep.value >= 0 ? config.steps[currentStep.value] : null,
  )
  const totalSteps = config.steps.length

  const storageKey = `${STORAGE_PREFIX}${config.pageKey}`

  function shouldShow(): boolean {
    return localStorage.getItem(storageKey) !== '1'
  }

  function start(): void {
    if (!shouldShow()) return
    currentStep.value = 0
  }

  function next(): void {
    if (currentStep.value < config.steps.length - 1) {
      currentStep.value++
    } else {
      finish()
    }
  }

  function prev(): void {
    if (currentStep.value > 0) {
      currentStep.value--
    }
  }

  function finish(): void {
    localStorage.setItem(storageKey, '1')
    currentStep.value = -1
  }

  function skip(): void {
    finish()
  }

  onMounted(() => {
    // 延迟启动，确保 DOM 渲染完成
    setTimeout(() => {
      start()
    }, 600)
  })

  return {
    currentStep,
    isActive,
    isFirst,
    isLast,
    currentStepData,
    totalSteps,
    next,
    prev,
    skip,
    finish,
    start,
    storageKey,
  }
}

/** 重置所有引导状态 */
export function resetAllTours(): void {
  const keysToRemove: string[] = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(STORAGE_PREFIX)) {
      keysToRemove.push(key)
    }
  }
  keysToRemove.forEach((k) => localStorage.removeItem(k))
}
