export interface DiseaseData {
  disease_name: string
  count: number
  year: number
  week: number
  report_date: string
  category: string
}

export interface TimeSeriesData {
  date: string
  value: number
}

export interface DiseaseTimeSeriesResponse {
  disease_name: string
  data: TimeSeriesData[]
  total_records: number
}

export interface SummaryData {
  total_records: number
  date_range: {
    start: string
    end: string
  }
  years_covered: number[]
  total_diseases: number
  disease_categories: Record<string, number>
  top_diseases: Record<string, number>
  yearly_totals: Record<string, number>
}

export interface TopDiseaseData {
  disease_name: string
  total_count: number
  category: string
}

export interface TopDiseasesResponse {
  top_diseases: TopDiseaseData[]
  year?: number
  total_diseases: number
}

export interface CategoryData {
  category: string
  total_count: number
  disease_count: number
}

export interface CategoriesResponse {
  categories: CategoryData[]
}

export interface YearlyTrendData {
  year: number
  total_count: number
}

export interface YearlyTrendsResponse {
  yearly_trends: YearlyTrendData[]
}

export interface HealthCheckResponse {
  status: string
  data_loaded: boolean
  records_count: number
  timestamp: string
}

export interface DiseasesResponse {
  diseases: string[]
}

export type ViewType = 'overview' | 'diseases' | 'categories' | 'trends'

export interface ChartDataPoint {
  x: string | number
  y: number
  label?: string
}