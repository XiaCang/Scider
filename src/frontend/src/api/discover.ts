import request from '../network/request'

export interface RecommendationItem {
  id: string
  title: string
  venue: string
  year: number
  reason: string
  relation: 'Trending' | 'Upstream' | 'Downstream'
}

export const fetchRecommendationsApi = (direction: string) =>
  request.get('/recommendations', { params: { direction } })

export const fetchCitationGraphApi = (doi: string) =>
  request.get('/recommendations/citations', { params: { doi } })
