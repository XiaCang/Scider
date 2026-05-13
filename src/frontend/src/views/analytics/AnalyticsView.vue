<template>
  <div class="analytics-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>📊 分析统计</h2>
      <p class="subtitle">基于您的文库数据进行多维度统计分析</p>
    </div>

    <!-- 文件夹选择器 -->
    <div class="folder-selector-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>选择分析范围</span>
            <el-button 
              type="primary" 
              :loading="analyzing"
              @click="handleAnalyze"
              :disabled="!hasSelectedFolders && !selectAllMode"
            >
              {{ analyzing ? '分析中...' : '开始分析' }}
            </el-button>
          </div>
        </template>

        <!-- 全选选项 -->
        <div class="select-all-option">
          <el-checkbox v-model="selectAllMode" @change="handleSelectAllChange">
            分析全部论文（不限制文件夹）
          </el-checkbox>
        </div>

        <!-- 文件夹树选择器 -->
        <div v-if="!selectAllMode" class="folder-tree-container">
          <el-tree
            ref="folderTreeRef"
            :data="folderTree"
            show-checkbox
            node-key="id"
            :props="{ label: 'name', children: 'children' }"
            @check="handleFolderCheck"
          />
        </div>

        <!-- 提示信息 -->
        <el-alert
          v-if="selectedFolderIds.length === 0 && !selectAllMode"
          title="请至少选择一个文件夹，或勾选「分析全部论文」"
          type="info"
          :closable="false"
          style="margin-top: 12px"
        />
      </el-card>
    </div>

    <!-- 分析结果展示区 -->
    <div v-if="statsData" class="results-section">
      <!-- 总览卡片 -->
      <el-row :gutter="16" class="overview-cards">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value">{{ statsData?.total_papers ?? 0 }}</div>
            <div class="stat-label">论文总数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value">{{ Object.keys(statsData?.authors || {}).length }}</div>
            <div class="stat-label">作者数量</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value">{{ Object.keys(statsData?.years || {}).length }}</div>
            <div class="stat-label">年份跨度</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value">{{ Object.keys(statsData?.venues || {}).length }}</div>
            <div class="stat-label">来源数量</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Tab 切换不同维度 -->
      <el-tabs v-model="activeTab" class="analysis-tabs">
        <!-- 作者分析 -->
        <el-tab-pane label="作者分析" name="author">
          <AuthorAnalysis ref="authorAnalysisRef" v-if="statsData" :data="statsData.authors || {}" />
        </el-tab-pane>

        <!-- 年份分析 -->
        <el-tab-pane label="年份趋势" name="year">
          <YearAnalysis ref="yearAnalysisRef" v-if="statsData" :data="statsData.years || {}" />
        </el-tab-pane>

        <!-- 期刊/会议分析 -->
        <el-tab-pane label="来源分析" name="venue">
          <VenueAnalysis ref="venueAnalysisRef" v-if="statsData" :data="statsData.venues || {}" />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-else
      description="请选择文件夹并点击「开始分析」"
      :image-size="200"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { useFolderStore } from '../../store/folder';
import { aggregateAnalyticsApi } from '../../api/analytics';
import type { AnalyticsStats } from '../../types/analytics';
import AuthorAnalysis from './components/AuthorAnalysis.vue';
import YearAnalysis from './components/YearAnalysis.vue';
import VenueAnalysis from './components/VenueAnalysis.vue';

const folderStore = useFolderStore();

// 状态
const analyzing = ref(false);
const statsData = ref<AnalyticsStats | null>(null);
const activeTab = ref('author');
const selectAllMode = ref(false);
const selectedFolderIds = ref<string[]>([]);
const folderTreeRef = ref();

// 子组件引用
const authorAnalysisRef = ref();
const yearAnalysisRef = ref();
const venueAnalysisRef = ref();

// 计算属性：是否有选中的文件夹
const hasSelectedFolders = computed(() => selectedFolderIds.value.length > 0);

// 计算属性：文件夹树数据（直接使用 folders）
const folderTree = computed(() => folderStore.folders);

// 处理全选变化
const handleSelectAllChange = (checked: boolean) => {
  if (checked) {
    selectedFolderIds.value = [];
    folderTreeRef.value?.setCheckedKeys([]);
  }
};

// 处理文件夹选择
const handleFolderCheck = () => {
  if (folderTreeRef.value) {
    selectedFolderIds.value = folderTreeRef.value.getCheckedKeys(true);
  }
};

// 执行分析
const handleAnalyze = async () => {
  if (!selectAllMode.value && selectedFolderIds.value.length === 0) {
    ElMessage.warning('请至少选择一个文件夹');
    return;
  }

  analyzing.value = true;
  
  try {
    const response = await aggregateAnalyticsApi({
      folder_ids: selectAllMode.value ? [] : selectedFolderIds.value
    });

    // request 拦截器返回的是 {code, data, msg} 结构，需要解构出 data
    statsData.value = response.data;
    ElMessage.success(`分析完成，共 ${response.data.total_papers} 篇论文`);
  } catch (error: any) {
    console.error('分析失败:', error);
    ElMessage.error(error.message || '网络错误，请稍后重试');
  } finally {
    analyzing.value = false;
  }
};

// 监听 Tab 切换，触发图表 resize
watch(activeTab, (newTab) => {
  // 延迟执行，确保 DOM 已更新
  setTimeout(() => {
    if (newTab === 'author') {
      authorAnalysisRef.value?.resize();
    } else if (newTab === 'year') {
      yearAnalysisRef.value?.resize();
    } else if (newTab === 'venue') {
      venueAnalysisRef.value?.resize();
    }
  }, 100);
});
</script>

<style scoped>
.analytics-view {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.folder-selector-section {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.select-all-option {
  margin-bottom: 16px;
}

.folder-tree-container {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
}

.overview-cards {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.analysis-tabs {
  margin-top: 24px;
}
</style>
