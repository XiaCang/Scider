<template>
  <div class="year-analysis">
    <!-- 数据表格 -->
    <el-table
      :data="sortedData"
      stripe
      style="width: 100%"
      max-height="300"
    >
      <el-table-column prop="year" label="年份" width="120" />
      <el-table-column prop="count" label="论文数量" width="120" sortable />
      <el-table-column label="占比">
        <template #default="{ row }">
          {{ ((row.count / totalCount) * 100).toFixed(1) }}%
        </template>
      </el-table-column>
    </el-table>

    <!-- 折线图 -->
    <div class="chart-container">
      <h3>研究热度趋势</h3>
      <div ref="chartRef" style="height: 400px"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';

interface Props {
  data: Record<number, number>;
}

const props = withDefaults(defineProps<Props>(), {
  data: () => ({})
});

const chartRef = ref<HTMLElement>();
let chartInstance: echarts.ECharts | null = null;

// 转换为数组并排序
const sortedData = computed(() => {
  if (!props.data || typeof props.data !== 'object') {
    return [];
  }
  return Object.entries(props.data)
    .map(([year, count]) => ({
      year: Number(year),
      count
    }))
    .sort((a, b) => a.year - b.year);
});

// 总论文数
const totalCount = computed(() => {
  if (!props.data || typeof props.data !== 'object') {
    return 0;
  }
  return Object.values(props.data).reduce((sum, val) => sum + val, 0);
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
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: sortedData.value.map(item => item.year),
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '论文数量'
    },
    series: [
      {
        name: '论文数量',
        type: 'line',
        data: sortedData.value.map(item => item.count),
        smooth: true,
        itemStyle: {
          color: '#67c23a'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
              { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
            ]
          }
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
.year-analysis {
  padding: 16px 0;
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
