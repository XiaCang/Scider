import request from '../network/request'

export interface LibraryPaper {
  id: string
  title: string
  authors: string
  year: number
  status: 'Processing' | 'Completed' | 'Awaiting Review'
  source: string
  keyPoints: string[]
}

export const fetchLibraryApi = () => request.get('/papers')

export const saveKeyPointsApi = (paperId: string, keyPoints: string[]) =>
  request.patch(`/papers/${paperId}/key-points`, { keyPoints })
