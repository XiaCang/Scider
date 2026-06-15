import { describe, it, expect, beforeEach } from 'vitest'

describe('useGuide', () => {
  const config = {
    pageKey: 'test-page',
    steps: [
      { selector: '#step-1', title: '第一步', description: '说明1', placement: 'bottom' as const },
      { selector: '#step-2', title: '第二步', description: '说明2' },
      { selector: '#step-3', title: '第三步', description: '说明3', placement: 'top' as const },
    ],
  }

  beforeEach(() => {
    localStorage.clear()
  })

  it('初始状态应为未激活', async () => {
    const { useGuide } = await import('./useGuide')
    const guide = useGuide(config)
    expect(guide.currentStep.value).toBe(-1)
    expect(guide.isActive.value).toBe(false)
    expect(guide.totalSteps).toBe(3)
  })

  it('start() 未完成引导时应激活第一步', async () => {
    const { useGuide } = await import('./useGuide')
    const guide = useGuide(config)
    guide.start()
    expect(guide.currentStep.value).toBe(0)
    expect(guide.isActive.value).toBe(true)
    expect(guide.isFirst.value).toBe(true)
    expect(guide.isLast.value).toBe(false)
    expect(guide.currentStepData.value?.title).toBe('第一步')
  })

  it('已完成引导时 start() 不应激活', async () => {
    localStorage.setItem('scider_tour_test-page', '1')
    const { useGuide } = await import('./useGuide')
    const guide = useGuide(config)
    guide.start()
    expect(guide.currentStep.value).toBe(-1)
    expect(guide.isActive.value).toBe(false)
  })

  it('next() 应前进到下一步', async () => {
    const { useGuide } = await import('./useGuide')
    const guide = useGuide(config)
    guide.start()
    expect(guide.currentStep.value).toBe(0)

    guide.next()
    expect(guide.currentStep.value).toBe(1)
    expect(guide.isFirst.value).toBe(false)
    expect(guide.isLast.value).toBe(false)

    guide.next()
    expect(guide.currentStep.value).toBe(2)
    expect(guide.isLast.value).toBe(true)
  })

  it('next() 在最后一步应完成引导', async () => {
    const { useGuide } = await import('./useGuide')
    const guide = useGuide(config)
    guide.start()
    guide.currentStep.value = 2 // 跳到最后一步
    guide.next()
    expect(guide.currentStep.value).toBe(-1)
    expect(guide.isActive.value).toBe(false)
    expect(localStorage.getItem('scider_tour_test-page')).toBe('1')
  })

  it('prev() 应后退一步', async () => {
    const { useGuide } = await import('./useGuide')
    const guide = useGuide(config)
    guide.start()
    guide.currentStep.value = 2
    guide.prev()
    expect(guide.currentStep.value).toBe(1)

    guide.prev()
    expect(guide.currentStep.value).toBe(0)

    guide.prev() // 已在第一步，不应变化
    expect(guide.currentStep.value).toBe(0)
  })

  it('skip() 应完成引导', async () => {
    const { useGuide } = await import('./useGuide')
    const guide = useGuide(config)
    guide.start()
    expect(guide.isActive.value).toBe(true)

    guide.skip()
    expect(guide.currentStep.value).toBe(-1)
    expect(guide.isActive.value).toBe(false)
    expect(localStorage.getItem('scider_tour_test-page')).toBe('1')
  })

  it('finish() 应完成引导并设置 localStorage', async () => {
    const { useGuide } = await import('./useGuide')
    const guide = useGuide(config)
    guide.start()
    guide.finish()
    expect(guide.currentStep.value).toBe(-1)
    expect(localStorage.getItem('scider_tour_test-page')).toBe('1')
  })

  it('currentStepData 当前无步骤时应返回 null', async () => {
    const { useGuide } = await import('./useGuide')
    const guide = useGuide(config)
    expect(guide.currentStepData.value).toBeNull()
  })

  it('currentStepData 应返回当前步骤数据', async () => {
    const { useGuide } = await import('./useGuide')
    const guide = useGuide(config)
    guide.currentStep.value = 1
    expect(guide.currentStepData.value?.title).toBe('第二步')
    expect(guide.currentStepData.value?.description).toBe('说明2')
    expect(guide.currentStepData.value?.selector).toBe('#step-2')
    expect(guide.currentStepData.value?.placement).toBeUndefined()
  })

  it('storageKey 应正确拼接', async () => {
    const { useGuide } = await import('./useGuide')
    const guide = useGuide(config)
    expect(guide.storageKey).toBe('scider_tour_test-page')
  })

  describe('resetAllTours', () => {
    it('应清除所有引导记录', async () => {
      localStorage.setItem('scider_tour_page-a', '1')
      localStorage.setItem('scider_tour_page-b', '1')
      localStorage.setItem('other_key', 'keep')

      const { resetAllTours } = await import('./useGuide')
      resetAllTours()

      expect(localStorage.getItem('scider_tour_page-a')).toBeNull()
      expect(localStorage.getItem('scider_tour_page-b')).toBeNull()
      expect(localStorage.getItem('other_key')).toBe('keep')
    })
  })
})
