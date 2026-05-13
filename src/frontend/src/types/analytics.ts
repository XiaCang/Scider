/**
 * 统计分析相关类型定义
 */

// 统计数据接口
export interface AnalyticsStats {
  total_papers: number;
  authors: Record<string, number>;      // {作者名: 频次}
  years: Record<number, number>;         // {年份: 数量}
  venues: Record<string, number>;        // {期刊/会议: 频次}
  message?: string;
}

// 聚合请求参数
export interface AggregateRequest {
  folder_ids: string[];
}

// 单维度统计结果
export type DimensionStats = Record<string, number> | Record<number, number>;

// 图表数据项
export interface ChartDataItem {
  name: string;
  value: number;
}
