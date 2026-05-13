<template>
  <div class="venue-analysis">
    <!-- 搜索工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索期刊/会议..."
        prefix-icon="Search"
        clearable
        style="width: 300px"
      />
    </div>

    <!-- 数据表格 -->
    <el-table
      :data="filteredData"
      stripe
      style="width: 100%; margin-top: 16px"
      max-height="400"
    >
      <el-table-column prop="name" label="来源" min-width="250" />
      <el-table-column prop="value" label="论文数量" width="120" sortable />
      <el-table-column label="占比">
        <template #default="{ row }">
          {{ ((row.value / totalCount) * 100).toFixed(1) }}%
        </template>
      </el-table-column>
    </el-table>

    <!-- 横向柱状图 -->
    <div class="chart-container">
      <h3>Top 10 热门来源</h3>
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

// 总论文数
const totalCount = computed(() => {
  if (!props.data || typeof props.data !== 'object') {
    return 0;
  }
  return Object.values(props.data).reduce((sum, val) => sum + val, 0);
});

// 过滤后的数据
const filteredData = computed(() => {
  if (!searchKeyword.value) {
    return dataArray.value.sort((a, b) => b.value - a.value);
  }

  const keyword = searchKeyword.value.toLowerCase();
  return dataArray.value
    .filter(item => item.name.toLowerCase().includes(keyword))
    .sort((a, b) => b.value - a.value);
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
      type: 'value',
      name: '论文数量'
    },
    yAxis: {
      type: 'category',
      data: top10Data.value.map(item => item.name).reverse(),
      axisLabel: {
        interval: 0
      }
    },
    series: [
      {
        name: '论文数量',
        type: 'bar',
        data: top10Data.value.map(item => item.value).reverse(),
        itemStyle: {
          color: '#e6a23c'
        },
        label: {
          show: true,
          position: 'right'
        }
      }
    ]
  };

  chartInstance.setOption(option);
};

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
.venue-analysis {
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
