<template>
  <div class="author-analysis">
    <!-- 搜索和排序工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索作者..."
        prefix-icon="Search"
        clearable
        style="width: 300px"
      />
      <el-select v-model="sortBy" placeholder="排序方式" style="width: 150px; margin-left: 12px">
        <el-option label="按频次降序" value="frequency_desc" />
        <el-option label="按频次升序" value="frequency_asc" />
        <el-option label="按姓名" value="name" />
      </el-select>
    </div>

    <!-- 数据表格 -->
    <el-table
      :data="filteredAndSortedData"
      stripe
      style="width: 100%; margin-top: 16px"
      max-height="400"
    >
      <el-table-column prop="name" label="作者" width="200" />
      <el-table-column prop="value" label="出现频次" width="120" sortable />
      <el-table-column label="占比">
        <template #default="{ row }">
          {{ ((row.value / totalPapers) * 100).toFixed(1) }}%
        </template>
      </el-table-column>
    </el-table>

    <!-- 柱状图 -->
    <div class="chart-container">
      <h3>Top 10 高产作者</h3>
      <div ref="chartRef" style="height: 400px"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';

interface Props {
  data: Record<string, number>;
}

const props = withDefaults(defineProps<Props>(), {
  data: () => ({})
});

const searchKeyword = ref('');
const sortBy = ref('frequency_desc');
const chartRef = ref<HTMLElement>();
let chartInstance: echarts.ECharts | null = null;

// 转换为数组格式
const dataArray = computed(() => {
  if (!props.data || typeof props.data !== 'object') {
    return [];
  }
  return Object.entries(props.data).map(([name, value]) => ({
    name,
    value
  }));
});

// 总论文数（用于计算占比）
const totalPapers = computed(() => {
  if (!props.data || typeof props.data !== 'object') {
    return 0;
  }
  return Object.values(props.data).reduce((sum, val) => sum + val, 0);
});

// 过滤和排序后的数据
const filteredAndSortedData = computed(() => {
  let result = [...dataArray.value];

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter(item => 
      item.name.toLowerCase().includes(keyword)
    );
  }

  // 排序
  switch (sortBy.value) {
    case 'frequency_desc':
      result.sort((a, b) => b.value - a.value);
      break;
    case 'frequency_asc':
      result.sort((a, b) => a.value - b.value);
      break;
    case 'name':
      result.sort((a, b) => a.name.localeCompare(b.name));
      break;
  }

  return result;
});

// Top 10 数据
const top10Data = computed(() => {
  return [...dataArray.value]
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);
});

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return;

  // 检查 DOM 尺寸
  const width = chartRef.value.clientWidth;
  const height = chartRef.value.clientHeight;
  
  if (width === 0 || height === 0) {
    // DOM 还未准备好，延迟初始化
    setTimeout(() => {
      initChart();
    }, 100);
    return;
  }

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }

  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: top10Data.value.map(item => item.name),
      axisLabel: {
        rotate: 45,
        interval: 0
      }
    },
    yAxis: {
      type: 'value',
      name: '频次'
    },
    series: [
      {
        name: '出现频次',
        type: 'bar',
        data: top10Data.value.map(item => item.value),
        itemStyle: {
          color: '#409eff'
        },
        label: {
          show: true,
          position: 'top'
        }
      }
    ]
  };

  chartInstance.setOption(option);
};

// 监听数据变化
watch(() => props.data, () => {
  nextTick(() => {
    initChart();
  });
}, { deep: true });

onMounted(() => {
  // 延迟初始化，确保 Tab 已激活且 DOM 已渲染
  nextTick(() => {
    setTimeout(() => {
      initChart();
    }, 50);
  });
  
  // 响应式调整
  window.addEventListener('resize', () => {
    chartInstance?.resize();
  });
});

// 暴露方法供父组件调用
defineExpose({
  resize: () => {
    chartInstance?.resize();
  }
});
</script>

<style scoped>
.author-analysis {
  padding: 16px 0;
}

.toolbar {
  display: flex;
  align-items: center;
}

.chart-container {
  margin-top: 32px;
}

.chart-container h3 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}
</style>
