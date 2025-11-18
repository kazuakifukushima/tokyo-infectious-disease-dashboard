'use client'

import { useState, useEffect, useMemo } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { apiClient } from '@/lib/api'
import LoadingSpinner from '../LoadingSpinner'
import type { DiseaseTimeSeriesResponse, DateRange } from '@/types'

ChartJS.register(
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
)

interface SentinelViewProps {
  dateRange: DateRange | null
}

export default function SentinelView({ dateRange }: SentinelViewProps) {
  const [diseases, setDiseases] = useState<string[]>([])
  const [selectedDisease, setSelectedDisease] = useState<string>('')
  const [timeSeriesData, setTimeSeriesData] = useState<DiseaseTimeSeriesResponse | null>(null)
  const [startYear, setStartYear] = useState<number>(2020)
  const [endYear, setEndYear] = useState<number>(2024)
  const [isLoading, setIsLoading] = useState(true)
  const [isChartLoading, setIsChartLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [aggregationMode, setAggregationMode] = useState<'weekly' | 'monthly' | 'yearly'>('weekly')
  const [summaryData, setSummaryData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedYears, setSelectedYears] = useState<number[]>([])
  const [yearlyData, setYearlyData] = useState<Record<number, DiseaseTimeSeriesResponse>>({})

  useEffect(() => {
    const fetchDiseases = async () => {
      try {
        setIsLoading(true)
        const data = await apiClient.getSentinelDiseases()
        if (data && data.diseases && data.diseases.length > 0) {
          setDiseases(data.diseases)
          setSelectedDisease(data.diseases[0])
        } else {
          console.warn('定点把握疾患リストが空です')
        }
      } catch (error) {
        console.error('定点把握疾患リスト取得エラー:', error)
        setDiseases([])
      } finally {
        setIsLoading(false)
      }
    }

    fetchDiseases()
  }, [])

  useEffect(() => {
    if (dateRange) {
      setStartYear(dateRange.startYear)
      setEndYear(dateRange.endYear)
      // 年毎比較用の選択年を設定
      const years: number[] = []
      for (let year = dateRange.startYear; year <= dateRange.endYear; year++) {
        years.push(year)
      }
      setSelectedYears(years.length > 0 ? years : [dateRange.endYear])
    } else {
      // デフォルト値: 過去5年間
      const currentYear = new Date().getFullYear()
      setStartYear(currentYear - 5)
      setEndYear(currentYear)
      // デフォルトで直近5年を選択
      const years: number[] = []
      for (let year = currentYear - 4; year <= currentYear; year++) {
        years.push(year)
      }
      setSelectedYears(years)
    }
  }, [dateRange])

  useEffect(() => {
    const fetchTimeSeries = async () => {
      if (!selectedDisease) {
        setTimeSeriesData(null)
        setYearlyData({})
        return
      }

      try {
        setIsChartLoading(true)
        
        // 年毎比較モード（週毎集計時のみ）
        if (aggregationMode === 'weekly' && selectedYears.length > 0) {
          const yearlyDataMap: Record<number, DiseaseTimeSeriesResponse> = {}
          
          // 各年のデータを取得
          for (const year of selectedYears) {
            try {
              const data = await apiClient.getSentinelDiseaseTimeSeries(
                selectedDisease,
                year,
                year
              )
              if (data && data.data) {
                yearlyDataMap[year] = data
              }
            } catch (err) {
              console.warn(`${year}年のデータ取得に失敗:`, err)
            }
          }
          
          setYearlyData(yearlyDataMap)
          
          // 全体のデータも取得（後方互換性のため）
          const data = await apiClient.getSentinelDiseaseTimeSeries(
            selectedDisease,
            startYear,
            endYear
          )
          if (data && data.data) {
            setTimeSeriesData(data)
          } else {
            setTimeSeriesData(null)
          }
        } else {
          // 通常モード
          const data = await apiClient.getSentinelDiseaseTimeSeries(
            selectedDisease,
            startYear,
            endYear
          )
          if (data && data.data) {
            setTimeSeriesData(data)
          } else {
            console.warn('時系列データが空です')
            setTimeSeriesData(null)
          }
          setYearlyData({})
        }
      } catch (error: any) {
        console.error('時系列データ取得エラー:', error)
        setError(error?.message || 'データの取得に失敗しました')
        setTimeSeriesData(null)
        setYearlyData({})
      } finally {
        setIsChartLoading(false)
      }
    }

    fetchTimeSeries()
  }, [selectedDisease, startYear, endYear, aggregationMode, selectedYears])

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const data = await apiClient.getSentinelSummary(startYear, endYear)
        setSummaryData(data)
      } catch (error) {
        console.error('サマリーデータ取得エラー:', error)
      }
    }

    fetchSummary()
  }, [startYear, endYear])

  // 検索フィルタリング
  const filteredDiseases = useMemo(() => {
    return diseases.filter(disease =>
      disease.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }, [diseases, searchQuery])

  // データの集約処理
  const aggregateData = useMemo(() => {
    if (!timeSeriesData || !timeSeriesData.data) return []

    const data = timeSeriesData.data

    if (aggregationMode === 'weekly') {
      return data
    }

    // 月毎または年毎に集約
    const grouped: Record<string, number> = {}

    data.forEach(item => {
      const dateStr = item.date
      let key: string

      if (aggregationMode === 'monthly') {
        // 年-週形式から年-月を抽出（簡易実装）
        const match = dateStr.match(/(\d{4})-W(\d+)/)
        if (match) {
          const year = parseInt(match[1])
          const week = parseInt(match[2])
          // 週から月を概算（1週目=1月、4週目=1月、など）
          const month = Math.min(12, Math.ceil(week / 4.33))
          key = `${year}-${month.toString().padStart(2, '0')}`
        } else {
          key = dateStr.substring(0, 7) // YYYY-MM形式
        }
      } else {
        // 年毎
        const match = dateStr.match(/(\d{4})/)
        key = match ? match[1] : dateStr.substring(0, 4)
      }

      if (!grouped[key]) {
        grouped[key] = 0
      }
      grouped[key] += item.value
    })

    return Object.entries(grouped)
      .map(([date, value]) => ({ date, value }))
      .sort((a, b) => a.date.localeCompare(b.date))
  }, [timeSeriesData, aggregationMode])

  // 年毎比較用のチャートデータ準備
  const yearlyComparisonChartData = useMemo(() => {
    if (aggregationMode !== 'weekly' || selectedYears.length === 0 || Object.keys(yearlyData).length === 0) {
      return null
    }

    // 週番号（1-52）をX軸に使用
    const weekLabels = Array.from({ length: 52 }, (_, i) => `第${i + 1}週`)
    
    // 各年のデータを週番号で整理
    const datasets = selectedYears.map((year, index) => {
      const yearData = yearlyData[year]
      if (!yearData || !yearData.data) {
        return null
      }

      // 週番号をキーにしたマップを作成
      const weekDataMap: Record<number, number> = {}
      yearData.data.forEach(item => {
        // date形式: "2024-W01" または "2024-01-01" など
        const weekMatch = item.date.match(/W(\d+)/)
        if (weekMatch) {
          const week = parseInt(weekMatch[1])
          weekDataMap[week] = (weekDataMap[week] || 0) + item.value
        } else {
          // 日付形式の場合、週番号を計算
          const dateMatch = item.date.match(/(\d{4})-(\d{2})-(\d{2})/)
          if (dateMatch) {
            const date = new Date(parseInt(dateMatch[1]), parseInt(dateMatch[2]) - 1, parseInt(dateMatch[3]))
            const week = getWeekNumber(date)
            weekDataMap[week] = (weekDataMap[week] || 0) + item.value
          }
        }
      })

      // 週番号順にデータを配列化
      const data = weekLabels.map((_, weekIndex) => {
        const week = weekIndex + 1
        return weekDataMap[week] || 0
      })

      // 色を生成（各年に異なる色を割り当て）
      const colors = [
        { border: 'rgb(59, 130, 246)', background: 'rgba(59, 130, 246, 0.1)' },
        { border: 'rgb(34, 197, 94)', background: 'rgba(34, 197, 94, 0.1)' },
        { border: 'rgb(239, 68, 68)', background: 'rgba(239, 68, 68, 0.1)' },
        { border: 'rgb(251, 146, 60)', background: 'rgba(251, 146, 60, 0.1)' },
        { border: 'rgb(168, 85, 247)', background: 'rgba(168, 85, 247, 0.1)' },
        { border: 'rgb(236, 72, 153)', background: 'rgba(236, 72, 153, 0.1)' },
        { border: 'rgb(14, 165, 233)', background: 'rgba(14, 165, 233, 0.1)' },
      ]
      const color = colors[index % colors.length]

      return {
        label: `${year}年`,
        data,
        borderColor: color.border,
        backgroundColor: color.background,
        tension: 0.1,
        fill: false,
      }
    }).filter(Boolean) as any[]

    return {
      labels: weekLabels,
      datasets,
    }
  }, [yearlyData, selectedYears, aggregationMode])

  // 週番号を計算する関数
  const getWeekNumber = (date: Date): number => {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
    const dayNum = d.getUTCDay() || 7
    d.setUTCDate(d.getUTCDate() + 4 - dayNum)
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
    return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
  }

  // チャートデータの準備
  const chartData = useMemo(() => {
    // 年毎比較モードの場合
    if (yearlyComparisonChartData) {
      return yearlyComparisonChartData
    }

    // 通常モード
    if (!aggregateData || aggregateData.length === 0) {
      return {
        labels: [],
        datasets: []
      }
    }

    return {
      labels: aggregateData.map(item => item.date),
      datasets: [
        {
          label: selectedDisease || '定点把握疾患',
          data: aggregateData.map(item => item.value),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.1,
        },
      ],
    }
  }, [aggregateData, selectedDisease, yearlyComparisonChartData])

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: aggregationMode === 'weekly' && selectedYears.length > 1
          ? `${selectedDisease || '定点把握疾患'} の年毎比較（週毎）`
          : `${selectedDisease || '定点把握疾患'} の発生動向（${aggregationMode === 'weekly' ? '週毎' : aggregationMode === 'monthly' ? '月毎' : '年毎'}）`,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: '報告数',
        },
      },
      x: {
        title: {
          display: true,
          text: aggregationMode === 'weekly' && selectedYears.length > 1 ? '週番号' : (aggregationMode === 'weekly' ? '週' : aggregationMode === 'monthly' ? '月' : '年'),
        },
      },
    },
  }

  // 統計情報の計算
  const statistics = useMemo(() => {
    if (!aggregateData || aggregateData.length === 0) return null

    const values = aggregateData.map(item => item.value)
    const total = values.reduce((sum, val) => sum + val, 0)
    const max = Math.max(...values)
    const min = Math.min(...values)
    const avg = Math.round(total / values.length)

    return { total, max, min, avg, count: values.length }
  }, [aggregateData])

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (diseases.length === 0) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">定点把握疾患分析</h2>
          <div className="text-center py-8">
            {error ? (
              <div className="text-red-600">
                <p className="mb-2">エラーが発生しました</p>
                <p className="text-sm text-gray-600">{error}</p>
              </div>
            ) : (
              <p className="text-gray-500">定点把握疾患データを読み込めませんでした。しばらく待ってから再読み込みしてください。</p>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">定点把握疾患分析</h2>
        <p className="text-gray-600 mb-6">
          季節性インフルエンザや新型コロナウイルス感染症（COVID-19）などの定点把握疾患の発生動向を分析します。
        </p>

        {/* 疾病選択と検索 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              定点把握疾患を選択
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="疾病名で検索..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <select
              value={selectedDisease}
              onChange={(e) => setSelectedDisease(e.target.value)}
              className="mt-2 w-full px-4 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {filteredDiseases.map((disease) => (
                <option key={disease} value={disease}>
                  {disease}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              集約モード
            </label>
            <select
              value={aggregationMode}
              onChange={(e) => {
                setAggregationMode(e.target.value as 'weekly' | 'monthly' | 'yearly')
                // 週毎以外の場合は年毎比較を無効化
                if (e.target.value !== 'weekly') {
                  setYearlyData({})
                }
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="weekly">週毎</option>
              <option value="monthly">月毎</option>
              <option value="yearly">年毎</option>
            </select>
          </div>
        </div>

        {/* 年毎比較設定（週毎モード時のみ） */}
        {aggregationMode === 'weekly' && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              年毎比較（複数選択可）
            </label>
            <div className="flex flex-wrap gap-2">
              {Array.from({ length: endYear - startYear + 1 }, (_, i) => startYear + i).map((year) => (
                <label key={year} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedYears.includes(year)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedYears([...selectedYears, year].sort())
                      } else {
                        setSelectedYears(selectedYears.filter(y => y !== year))
                      }
                    }}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-900">{year}年</span>
                </label>
              ))}
            </div>
            {selectedYears.length === 0 && (
              <p className="mt-2 text-sm text-yellow-600">少なくとも1つの年を選択してください</p>
            )}
          </div>
        )}

        {/* 統計情報 */}
        {statistics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">総報告数</div>
              <div className="text-2xl font-bold text-gray-900">{statistics.total.toLocaleString()}</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">最大値</div>
              <div className="text-2xl font-bold text-gray-900">{statistics.max.toLocaleString()}</div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">最小値</div>
              <div className="text-2xl font-bold text-gray-900">{statistics.min.toLocaleString()}</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">平均値</div>
              <div className="text-2xl font-bold text-gray-900">{statistics.avg.toLocaleString()}</div>
            </div>
          </div>
        )}

        {/* 時系列グラフ */}
        {isChartLoading ? (
          <LoadingSpinner />
        ) : (
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <div style={{ height: '400px' }}>
              {chartData.labels.length > 0 ? (
                <Line data={chartData} options={chartOptions} />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  データがありません
                </div>
              )}
            </div>
          </div>
        )}

        {/* データ詳細テーブル */}
        {aggregateData && aggregateData.length > 0 && (
          <div className="mt-6 bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">データ詳細</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-900 uppercase tracking-wider">
                      {aggregationMode === 'weekly' ? '週' : aggregationMode === 'monthly' ? '月' : '年'}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-900 uppercase tracking-wider">
                      報告数
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {aggregateData.map((item, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.date}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.value.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

