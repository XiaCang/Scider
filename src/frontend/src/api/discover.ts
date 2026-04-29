import instance from '../network/request'

export interface RecommendationItem {
  id: string
  title: string
  venue: string
  year: number
  reason: string
  relation: 'Trending' | 'Upstream' | 'Downstream'
}

export const fetchRecommendationsApi = (direction: string) =>
  instance.get('/recommendations', { params: { direction } })

export const fetchCitationGraphApi = (doi: string) =>
  instance.get('/recommendations/citations', { params: { doi } })
