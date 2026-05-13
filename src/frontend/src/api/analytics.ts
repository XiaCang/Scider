/**
 * 统计分析 API 调用
 */
import request from '../network/request';
import type { AnalyticsStats, AggregateRequest, DimensionStats } from '../types/analytics';
import type { ApiResponse } from '../types/auth';

/**
 * 聚合统计数据
 */
export const aggregateAnalyticsApi = (data: AggregateRequest) => {
  return request.post<ApiResponse<AnalyticsStats>>('/analytics/aggregate', data);
};

/**
 * 获取特定维度的统计数据
 * @param dimension 维度: 'author' | 'year' | 'venue'
 * @param folderIds 文件夹ID列表
 */
export const getDimensionStatsApi = (
  dimension: string,
  folderIds: string[] = []
) => {
  const folderIdsJson = JSON.stringify(folderIds);
  return request.get<ApiResponse<DimensionStats>>(
    `/analytics/stats/${dimension}`,
    { params: { folder_ids: folderIdsJson } }
  );
};