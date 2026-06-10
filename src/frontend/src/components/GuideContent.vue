<script setup lang="ts">
import {
  Collection,
  ChatDotRound,
  Search,
  Connection,
  TopRight,
  Setting,
} from '@element-plus/icons-vue'

interface GuideItem {
  icon: any
  title: string
  desc: string
  tips: string[]
}

const guideItems: GuideItem[] = [
  {
    icon: Collection,
    title: '我的文库',
    desc: '集中管理你的论文收藏，轻松分类与检索',
    tips: [
      '上传 PDF 论文，系统将自动解析元数据',
      '创建文件夹，按课题或类别整理论文',
      '点击论文查看/编辑四维度关键点（背景、方法、创新点、结论）',
    ],
  },
  {
    icon: ChatDotRound,
    title: 'AI 对话',
    desc: '智能助手为你的论文研究提供深度支持',
    tips: [
      '在 PDF 预览页面打开 AI 对话侧栏',
      '对论文内容自由提问，获取流式智能回答',
      '一键提取论文四要素，快速把握文章核心',
    ],
  },
  {
    icon: Search,
    title: '发现论文',
    desc: '探索你感兴趣的研究方向和最新文献',
    tips: [
      '输入关键词搜索相关领域论文',
      '浏览论文基本信息与关键数据',
      '收藏有价值的论文到你的文库中',
    ],
  },
  {
    icon: TopRight,
    title: '上下游分析',
    desc: '追踪论文的引用脉络与研究演进',
    tips: [
      '查看目标论文引用了哪些前序研究',
      '了解后续研究如何基于该论文发展',
      '构建论文的上下游引用关系链',
    ],
  },
  {
    icon: Connection,
    title: '知识图谱',
    desc: '可视化你的论文关系网络',
    tips: [
      '以图谱形式展示论文之间的引用关系',
      '直观了解研究领域的知识结构',
      '发现关键节点论文与研究脉络',
    ],
  },
  {
    icon: Setting,
    title: '设置',
    desc: '个性化配置你的使用体验',
    tips: [
      '修改个人资料与登录密码',
      '配置 AI 模型提供商参数',
      '管理你的账号安全设置',
    ],
  },
]
</script>

<template>
  <div class="guide-content">
    <!-- 头部 -->
    <div class="guide-header">
      <h1 class="guide-header__title">使用指南</h1>
      <p class="guide-header__subtitle">快速了解 Scider 的核心功能，开启你的智能文献管理之旅</p>
    </div>

    <!-- 功能卡片列表 -->
    <div class="guide-grid">
      <div
        v-for="item in guideItems"
        :key="item.title"
        class="guide-card"
      >
        <div class="guide-card__head">
          <span class="guide-card__icon">
            <el-icon :size="22">
              <component :is="item.icon" />
            </el-icon>
          </span>
          <span class="guide-card__title">{{ item.title }}</span>
        </div>
        <p class="guide-card__desc">{{ item.desc }}</p>
        <ul class="guide-card__tips">
          <li v-for="tip in item.tips" :key="tip">{{ tip }}</li>
        </ul>
      </div>
    </div>

    <!-- 底部提示 -->
    <div class="guide-footer">
      <p>Scider — 智能学术论文管理，让科研更高效</p>
    </div>
  </div>
</template>

<style scoped>
.guide-content {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
  padding: 0 16px;
}

/* ── 头部 ── */
.guide-header {
  text-align: center;
  padding: 32px 0 28px;
}

.guide-header__icon {
  display: inline-flex;
  margin-bottom: 12px;
}

.guide-header__title {
  margin: 0;
  font-size: 1.65rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.guide-header__subtitle {
  margin: 8px 0 0;
  font-size: 0.92rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* ── 功能卡片网格 ── */
.guide-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding-bottom: 24px;
}

.guide-card {
  background: var(--bg-solid, #fff);
  border: 1px solid var(--line-soft, rgba(0,0,0,0.06));
  border-radius: 14px;
  padding: 20px;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.guide-card:hover {
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.06);
  border-color: rgba(74, 157, 154, 0.2);
}

.guide-card__head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.guide-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(74, 157, 154, 0.08);
  color: var(--brand, #4a9d9a);
  flex-shrink: 0;
}

.guide-card__title {
  font-size: 0.95rem;
  font-weight: 650;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.guide-card__desc {
  margin: 0 0 10px;
  font-size: 0.82rem;
  color: var(--text-secondary);
  line-height: 1.45;
}

.guide-card__tips {
  margin: 0;
  padding: 0;
  list-style: none;
}

.guide-card__tips li {
  position: relative;
  padding: 3px 0 3px 16px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.guide-card__tips li::before {
  content: '';
  position: absolute;
  left: 2px;
  top: 10px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--brand, #4a9d9a);
  opacity: 0.5;
}

/* ── 底部 ── */
.guide-footer {
  text-align: center;
  padding: 16px 0 32px;
}

.guide-footer p {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .guide-grid {
    grid-template-columns: 1fr;
  }

  .guide-header {
    padding: 20px 0 20px;
  }

  .guide-header__title {
    font-size: 1.35rem;
  }
}
</style>
