/** 年份筛选选项 */
export const yearOptions = [
  { label: '全部年份', value: '' },
  { label: '2025', value: '2025' },
  { label: '2024', value: '2024' },
  { label: '2023', value: '2023' },
  { label: '2022', value: '2022' },
  { label: '2021及更早', value: '2021' },
]

/** 来源/会议筛选选项 */
export const venueOptions = [
  { label: '全部来源', value: '' },
  { label: 'arXiv', value: 'arXiv' },
  { label: 'SIGIR', value: 'SIGIR' },
  { label: 'CHI', value: 'CHI' },
  { label: 'ACL', value: 'ACL' },
  { label: 'NeurIPS', value: 'NeurIPS' },
]

/** 排序选项 */
export const sortOptions = [
  { label: '相关性', value: 'relevance' },
  { label: '最新发表', value: 'year-desc' },
  { label: '最早发表', value: 'year-asc' },
  { label: '标题 A-Z', value: 'title-asc' },
]
