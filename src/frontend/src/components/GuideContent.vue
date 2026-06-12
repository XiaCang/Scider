<script setup lang="ts">
import { reactive } from 'vue'
import {
  Collection,
  ChatDotRound,
  Search,
  Connection,
  Setting,
  EditPen,
  UserFilled,
  Reading,
  ArrowDown,
  Document,
  FolderOpened,
  Link,
  TopRight,
} from '@element-plus/icons-vue'

/* ── 功能卡片 ── */
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
    desc: '集中管理你的论文收藏，轻松分类、检索与确认入库',
    tips: [
      '拖拽上传 PDF，系统异步解析元数据与四维度关键点',
      '创建文件夹按课题整理，支持多选批量删除/移动',
      '论文状态流转：解析中 → 待确认 → 已确认',
      '确认后的论文内容作为知识图谱构建输入',
    ],
  },
  {
    icon: ChatDotRound,
    title: 'AI 问答助手',
    desc: '基于论文内容与知识图谱的智能分析助手',
    tips: [
      'PDF 场景：基于当前论文内容 + 用户笔记流式回答',
      '图谱场景：基于图谱论文节点流式回答',
      '采用 RAG 技术确保回答准确、贴合论文原文',
    ],
  },
  {
    icon: Search,
    title: '发现论文',
    desc: '多维度探索前沿研究，构建个人学术脉络',
    tips: [
      '关键词检索：调用学术 API 搜索相关领域论文',
      '上下游检索：查看目标论文的参考文献与引用文献',
      '方向推荐：基于文库论文向量均值智能推荐相似论文',
      '支持单篇/批量导入论文到文库',
    ],
  },
  {
    icon: Connection,
    title: '知识图谱',
    desc: 'LLM 自动生成，可视化你的个人学术知识网络',
    tips: [
      '选择文件夹自动生成力导向图，节点按主题聚类着色',
      'LLM 分析图结构，输出聚类信息与语义关联边',
      '支持手动编辑：添加/删除节点与边、编辑节点属性',
      '点击节点查看四要素摘要与关联论文；导出 PNG/SVG',
    ],
  },
  {
    icon: Reading,
    title: 'PDF 阅读与标注',
    desc: '增强型论文阅读器，辅助深度研读',
    tips: [
      '连续滚动模式浏览全文，页码输入框快速定位跳转',
      '文档内文字搜索，匹配结果高亮并支持遍历跳转',
      '文本选区高亮标注，标注数据持久化保存与恢复',
      '右侧要点侧边栏，四要素对照阅读辅助理解',
    ],
  },
  {
    icon: EditPen,
    title: '笔记与知识管理',
    desc: '富文本/Markdown 笔记，联动 PDF 批注',
    tips: [
      '支持 Markdown 语法、LaTeX 数学公式、图片粘贴上传',
      '按论文分组管理笔记，全文搜索快速定位',
      '笔记批注与 PDF 位置联动，点击即跳转',
      '支持导出 Markdown / TXT / PDF 文件',
    ],
  },
  {
    icon: UserFilled,
    title: '个人中心',
    desc: '管理账户信息与个性化偏好',
    tips: [
      '修改昵称与上传头像，支持 JPG/PNG 格式',
      '密码修改需验证原密码，密码重置全流程支持',
      '账户注销需二次密码验证，数据 7 天内可恢复',
    ],
  },
  {
    icon: Setting,
    title: '系统设置',
    desc: '配置 AI 模型提供商与系统参数',
    tips: [
      '多模型提供商列表，支持增删改查 API 密钥',
      'API 密钥加密存储，前端仅显示脱敏标识',
      '设置默认模型，自由切换 AI 服务商',
    ],
  },
]

/* ── 展开/折叠状态 ── */
const expandedMap = reactive<Record<number, boolean>>({})

function toggleExpand(idx: number): void {
  expandedMap[idx] = !expandedMap[idx]
}

/* ── 外部资源链接 ── */
interface ResourceLink {
  icon: any
  label: string
  desc: string
  url: string
}

const resourceLinks: ResourceLink[] = [
  {
    icon: Document,
    label: '团队博客',
    desc: '了解项目开发历程与团队动态',
    url: 'https://www.cnblogs.com/BBnomoney',
  },
  {
    icon: FolderOpened,
    label: '开源代码仓库',
    desc: 'GitHub 源码、Issue 与 Release',
    url: 'https://github.com/XiaCang/Scider',
  },
  {
    icon: Link,
    label: '宣传页面',
    desc: 'Scider 产品介绍与快速入口',
    url: 'https://qingxin14.github.io/scider/',
  },
]
</script>

<template>
  <div class="guide-content">
    <!-- 头部 -->
    <div class="guide-header">
      <h1 class="guide-header__title">使用指南</h1>
      <p class="guide-header__subtitle">快速了解 Scider 的核心概念与功能，开启你的智能文献管理之旅</p>
    </div>

    <!-- 功能卡片区 -->
    <section class="guide-section">
      <h2 class="guide-section__title">功能详情</h2>
      <div class="guide-list">
        <div
          v-for="(item, idx) in guideItems"
          :key="item.title"
          class="guide-row"
          :class="{ 'is-expanded': expandedMap[idx] }"
          @click="toggleExpand(idx)"
        >
          <div class="guide-row__bar">
            <span class="guide-row__icon">
              <el-icon :size="20">
                <component :is="item.icon" />
              </el-icon>
            </span>
            <span class="guide-row__title">{{ item.title }}</span>
            <span class="guide-row__arrow" :class="{ 'is-flipped': expandedMap[idx] }">
              <el-icon :size="16"><ArrowDown /></el-icon>
            </span>
          </div>
          <div class="guide-row__body">
            <p class="guide-row__desc">{{ item.desc }}</p>
            <ul class="guide-row__tips">
              <li v-for="tip in item.tips" :key="tip">{{ tip }}</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- 外部资源 -->
    <section class="guide-section">
      <h2 class="guide-section__title">更多资源</h2>
      <div class="resource-grid">
        <a
          v-for="r in resourceLinks"
          :key="r.url"
          :href="r.url"
          target="_blank"
          rel="noopener noreferrer"
          class="resource-card"
        >
          <span class="resource-card__icon">
            <el-icon :size="22">
              <component :is="r.icon" />
            </el-icon>
          </span>
          <div class="resource-card__body">
            <span class="resource-card__label">{{ r.label }}</span>
            <span class="resource-card__desc">{{ r.desc }}</span>
          </div>
          <el-icon :size="14" class="resource-card__external"><TopRight /></el-icon>
        </a>
      </div>
    </section>

    <!-- 底部提示 -->
    <div class="guide-footer">
      <p>Scider — 智能学术论文管理，让科研更高效</p>
    </div>
  </div>
</template>

<style scoped>
.guide-content {
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  padding: 0 16px;
}

/* ── 头部 ── */
.guide-header {
  text-align: center;
  padding: 40px 0 20px;
}

.guide-header__title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.guide-header__subtitle {
  margin: 8px 0 0;
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* ── 章节通用 ── */
.guide-section {
  padding: 12px 0 8px;
}

.guide-section__title {
  margin: 0 0 16px;
  font-size: 1.1rem;
  font-weight: 650;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--line-soft, rgba(0, 0, 0, 0.06));
}

/* ── 功能卡片列表（手风琴） ── */
.guide-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 16px;
}

.guide-row {
  background: var(--bg-solid, #fff);
  border: 1px solid var(--line-soft, rgba(0, 0, 0, 0.06));
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.guide-row:hover {
  border-color: rgba(74, 157, 154, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.guide-row.is-expanded {
  border-color: rgba(74, 157, 154, 0.25);
  box-shadow: 0 4px 20px rgba(74, 157, 154, 0.08);
}

/* ── 顶栏（始终可见） ── */
.guide-row__bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  user-select: none;
}

.guide-row__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: rgba(74, 157, 154, 0.08);
  color: var(--brand, #4a9d9a);
  flex-shrink: 0;
}

.guide-row__title {
  font-size: 0.92rem;
  font-weight: 650;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  flex: 1;
}

.guide-row__arrow {
  display: flex;
  align-items: center;
  color: var(--text-tertiary);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.guide-row__arrow.is-flipped {
  transform: rotate(180deg);
}

/* ── 展开内容 ── */
.guide-row__body {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1), padding 0.35s ease;
  padding: 0 18px;
  border-top: 1px solid transparent;
  transition-property: max-height, padding, border-color;
}

.guide-row.is-expanded .guide-row__body {
  max-height: 300px;
  padding: 14px 18px;
  border-top-color: var(--line-soft, rgba(0, 0, 0, 0.05));
}

.guide-row__desc {
  margin: 0 0 10px;
  font-size: 0.82rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.guide-row__tips {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 20px;
}

.guide-row__tips li {
  position: relative;
  padding: 4px 0 4px 18px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.guide-row__tips li::before {
  content: '';
  position: absolute;
  left: 4px;
  top: 11px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--brand, #4a9d9a);
  opacity: 0.5;
}

/* ── 外部资源链接 ── */
.resource-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding-bottom: 16px;
}

.resource-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-solid, #fff);
  border: 1px solid var(--line-soft, rgba(0, 0, 0, 0.06));
  border-radius: 12px;
  padding: 16px 18px;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.resource-card:hover {
  border-color: rgba(74, 157, 154, 0.25);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  transform: translateY(-1px);
}

.resource-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(74, 157, 154, 0.08);
  color: var(--brand, #4a9d9a);
  flex-shrink: 0;
}

.resource-card__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.resource-card__label {
  font-size: 0.88rem;
  font-weight: 650;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.resource-card__desc {
  font-size: 0.76rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.resource-card__external {
  color: var(--text-tertiary);
  flex-shrink: 0;
  transition: color 0.2s ease;
}

.resource-card:hover .resource-card__external {
  color: var(--brand, #4a9d9a);
}

/* ── 底部 ── */
.guide-footer {
  text-align: center;
  padding: 16px 0 40px;
}

.guide-footer p {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .guide-row__tips {
    grid-template-columns: 1fr;
  }

  .resource-grid {
    grid-template-columns: 1fr;
  }

  .guide-header {
    padding: 24px 0 16px;
  }

  .guide-header__title {
    font-size: 1.4rem;
  }

  .guide-section__title {
    font-size: 1rem;
  }

  .guide-row__bar {
    padding: 12px 14px;
    gap: 10px;
  }

  .guide-row.is-expanded .guide-row__body {
    padding: 12px 14px;
  }
}
</style>
