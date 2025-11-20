import axios from 'axios'
import type {
  SummaryData,
  DiseaseTimeSeriesResponse,
  TopDiseasesResponse,
  CategoriesResponse,
  YearlyTrendsResponse,
  HealthCheckResponse,
  DiseasesResponse,
  DateRange
} from '@/types'
import { 
  loadStaticSummaryData, 
  loadStaticDiseaseList, 
  loadStaticSentinelDiseaseList,
  loadStaticDiseaseTimeSeries,
  loadStaticSentinelDiseaseTimeSeries
} from './staticData'

// 本番環境では /api 経由でアクセス、開発環境では localhost:8000 を使用
const getApiBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }
  if (typeof window !== 'undefined') {
    // ブラウザ環境: 本番環境では /api、開発環境では localhost:8000
    return window.location.hostname === 'localhost' ? 'http://localhost:8000' : '/api'
  }
  // サーバーサイド: localhost:8000
  return 'http://localhost:8000'
}

const API_BASE_URL = getApiBaseUrl()

const apiInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    console.error('API Error:', error)
    
    // Vercel環境でAPI接続に失敗した場合、静的データファイルから読み込む
    if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
      // 本番環境でAPI接続エラーの場合、静的ファイルから読み込む
      if (error.request || (error.response && error.response.status >= 500)) {
        console.warn('API接続に失敗しました。静的データファイルから読み込みます。')
        // エラーを再スローして、呼び出し側で処理できるようにする
      }
    }
    
    if (error.response) {
      throw new Error(`API Error: ${error.response.status} - ${error.response.data?.detail || error.response.statusText}`)
    } else if (error.request) {
      throw new Error('ネットワークエラー: サーバーに接続できません')
    } else {
      throw new Error(`リクエストエラー: ${error.message}`)
    }
  }
)

export const apiClient = {
  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await apiInstance.get<HealthCheckResponse>('/health')
    return response.data
  },

  async getSummary(dateRange?: DateRange): Promise<SummaryData> {
    try {
      const params = new URLSearchParams()
      if (dateRange) {
        params.append('start_year', dateRange.startYear.toString())
        params.append('end_year', dateRange.endYear.toString())
      }
      
      const url = dateRange ? `/summary?${params.toString()}` : '/summary'
      const response = await apiInstance.get<SummaryData>(url)
      return response.data
    } catch (error: any) {
      // Vercel環境またはAPI接続に失敗した場合、静的データから読み込む
      const isVercelEnv = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
      const isNetworkError = error.message?.includes('ネットワークエラー') || 
                            error.message?.includes('接続できません') ||
                            error.code === 'ECONNREFUSED' ||
                            error.code === 'ERR_NETWORK' ||
                            (error.response && error.response.status >= 500) ||
                            !error.response
      
      if (isVercelEnv || isNetworkError) {
        console.warn('API接続に失敗したため、静的データから読み込みます', error.message)
        try {
          const staticData = await loadStaticSummaryData()
          if (staticData) {
            return staticData
          }
        } catch (staticError) {
          console.error('静的データの読み込みにも失敗しました', staticError)
        }
      }
      throw error
    }
  },

  async getDiseases(): Promise<DiseasesResponse> {
    try {
      const response = await apiInstance.get<DiseasesResponse>('/diseases')
      return response.data
    } catch (error: any) {
      // Vercel環境またはAPI接続に失敗した場合、静的データから読み込む
      const isVercelEnv = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
      const isNetworkError = error.message?.includes('ネットワークエラー') || 
                            error.message?.includes('接続できません') ||
                            error.code === 'ECONNREFUSED' ||
                            error.code === 'ERR_NETWORK' ||
                            (error.response && error.response.status >= 500) ||
                            !error.response
      
      if (isVercelEnv || isNetworkError) {
        console.warn('API接続に失敗したため、静的データから読み込みます', error.message)
        try {
          const staticList = await loadStaticDiseaseList()
          if (staticList) {
            return { diseases: staticList }
          }
        } catch (staticError) {
          console.error('静的データの読み込みにも失敗しました', staticError)
        }
      }
      throw error
    }
  },

  async getDiseaseTimeSeries(
    diseaseName: string,
    startYear?: number,
    endYear?: number
  ): Promise<DiseaseTimeSeriesResponse> {
    try {
      const params = new URLSearchParams()
      if (startYear) params.append('start_year', startYear.toString())
      if (endYear) params.append('end_year', endYear.toString())
      
      const url = `/diseases/${encodeURIComponent(diseaseName)}/timeseries`
      const response = await apiInstance.get<DiseaseTimeSeriesResponse>(
        `${url}?${params.toString()}`
      )
      return response.data
    } catch (error: any) {
      // Vercel環境またはAPI接続に失敗した場合、静的データから読み込む
      const isVercelEnv = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
      const isNetworkError = error.message?.includes('ネットワークエラー') || 
                            error.message?.includes('接続できません') ||
                            error.code === 'ECONNREFUSED' ||
                            error.code === 'ERR_NETWORK' ||
                            (error.response && error.response.status >= 500) ||
                            !error.response
      
      if (isVercelEnv || isNetworkError) {
        console.warn('API接続に失敗したため、静的データから読み込みます', error.message)
        try {
          const staticData = await loadStaticDiseaseTimeSeries(diseaseName, startYear, endYear)
          if (staticData) {
            return staticData as DiseaseTimeSeriesResponse
          }
        } catch (staticError) {
          console.error('静的データの読み込みにも失敗しました', staticError)
        }
      }
      throw error
    }
  },

  async getTopDiseases(
    limit = 10, 
    year?: number, 
    startYear?: number, 
    endYear?: number
  ): Promise<TopDiseasesResponse> {
    const params = new URLSearchParams()
    params.append('limit', limit.toString())
    if (year) params.append('year', year.toString())
    if (startYear) params.append('start_year', startYear.toString())
    if (endYear) params.append('end_year', endYear.toString())
    
    const response = await apiInstance.get<TopDiseasesResponse>(
      `/diseases/top?${params.toString()}`
    )
    return response.data
  },

  async getCategories(dateRange?: DateRange): Promise<CategoriesResponse> {
    const params = new URLSearchParams()
    if (dateRange) {
      params.append('start_year', dateRange.startYear.toString())
      params.append('end_year', dateRange.endYear.toString())
    }
    
    const url = dateRange ? `/categories?${params.toString()}` : '/categories'
    const response = await apiInstance.get<CategoriesResponse>(url)
    return response.data
  },

  async getYearlyTrends(
    startYear?: number, 
    endYear?: number
  ): Promise<YearlyTrendsResponse> {
    const params = new URLSearchParams()
    if (startYear !== undefined) params.append('start_year', startYear.toString())
    if (endYear !== undefined) params.append('end_year', endYear.toString())
    
    const url = params.toString() ? `/yearly-trends?${params.toString()}` : '/yearly-trends'
    const response = await apiInstance.get<YearlyTrendsResponse>(url)
    return response.data
  },

  async reloadData(): Promise<{ message: string; records_count: number; timestamp: string }> {
    const response = await apiInstance.get('/reload-data')
    return response.data
  },

  // 定点把握疾患用API
  async getSentinelSummary(
    startYear?: number,
    endYear?: number
  ): Promise<any> {
    const params = new URLSearchParams()
    if (startYear !== undefined) params.append('start_year', startYear.toString())
    if (endYear !== undefined) params.append('end_year', endYear.toString())
    
    const url = params.toString() ? `/sentinel/summary?${params.toString()}` : '/sentinel/summary'
    const response = await apiInstance.get(url)
    return response.data
  },

  async getSentinelDiseases(): Promise<{ diseases: string[] }> {
    try {
      const response = await apiInstance.get('/sentinel/diseases')
      return response.data
    } catch (error: any) {
      // Vercel環境またはAPI接続に失敗した場合、静的データから読み込む
      const isVercelEnv = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
      const isNetworkError = error.message?.includes('ネットワークエラー') || 
                            error.message?.includes('接続できません') ||
                            error.code === 'ECONNREFUSED' ||
                            error.code === 'ERR_NETWORK' ||
                            (error.response && error.response.status >= 500) ||
                            !error.response
      
      if (isVercelEnv || isNetworkError) {
        console.warn('API接続に失敗したため、静的データから読み込みます', error.message)
        try {
          const staticList = await loadStaticSentinelDiseaseList()
          if (staticList) {
            return { diseases: staticList }
          }
        } catch (staticError) {
          console.error('静的データの読み込みにも失敗しました', staticError)
        }
      }
      throw error
    }
  },

  async getSentinelDiseaseTimeSeries(
    diseaseName: string,
    startYear?: number,
    endYear?: number
  ): Promise<DiseaseTimeSeriesResponse> {
    try {
      const params = new URLSearchParams()
      if (startYear !== undefined) params.append('start_year', startYear.toString())
      if (endYear !== undefined) params.append('end_year', endYear.toString())
      
      const url = `/sentinel/diseases/${encodeURIComponent(diseaseName)}/timeseries`
      const response = await apiInstance.get<DiseaseTimeSeriesResponse>(
        `${url}?${params.toString()}`
      )
      return response.data
    } catch (error: any) {
      // Vercel環境またはAPI接続に失敗した場合、静的データから読み込む
      const isVercelEnv = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
      const isNetworkError = error.message?.includes('ネットワークエラー') || 
                            error.message?.includes('接続できません') ||
                            error.code === 'ECONNREFUSED' ||
                            error.code === 'ERR_NETWORK' ||
                            (error.response && error.response.status >= 500) ||
                            !error.response
      
      if (isVercelEnv || isNetworkError) {
        console.warn('API接続に失敗したため、静的データから読み込みます', error.message)
        try {
          const staticData = await loadStaticSentinelDiseaseTimeSeries(diseaseName, startYear, endYear)
          if (staticData) {
            return staticData as DiseaseTimeSeriesResponse
          }
        } catch (staticError) {
          console.error('静的データの読み込みにも失敗しました', staticError)
        }
      }
      throw error
    }
  },

  async getSentinelTopDiseases(
    limit = 10,
    year?: number,
    startYear?: number,
    endYear?: number
  ): Promise<any> {
    const params = new URLSearchParams()
    params.append('limit', limit.toString())
    if (year !== undefined) params.append('year', year.toString())
    if (startYear !== undefined) params.append('start_year', startYear.toString())
    if (endYear !== undefined) params.append('end_year', endYear.toString())
    
    const response = await apiInstance.get(
      `/sentinel/diseases/top?${params.toString()}`
    )
    return response.data
  },

  async getSentinelYearlyTrends(
    startYear?: number,
    endYear?: number
  ): Promise<YearlyTrendsResponse> {
    const params = new URLSearchParams()
    if (startYear !== undefined) params.append('start_year', startYear.toString())
    if (endYear !== undefined) params.append('end_year', endYear.toString())
    
    const url = params.toString() ? `/sentinel/yearly-trends?${params.toString()}` : '/sentinel/yearly-trends'
    const response = await apiInstance.get<YearlyTrendsResponse>(url)
    return response.data
  }
}

export default apiClient