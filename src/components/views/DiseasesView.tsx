'use client'

import { useState, useEffect, useMemo } from 'react'
import dynamic from 'next/dynamic'
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
import type { DiseasesResponse, DiseaseTimeSeriesResponse, DateRange } from '@/types'

// Chart.jsをクライアントサイドでのみ読み込む
const Line = dynamic(() => import('react-chartjs-2').then((mod) => mod.Line), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center h-64"><LoadingSpinner /></div>
})

ChartJS.register(
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
)

interface DiseasesViewProps {
  dateRange: DateRange | null
}

// 感染症の法定分類定義（厚生労働省の感染症法に基づく）
const DISEASE_CATEGORIES: Record<string, string[]> = {
  "1類感染症": [
    "エボラ出血熱", "クリミア・コンゴ出血熱", "痘そう", "南米出血熱", 
    "ペスト", "マールブルグ病", "ラッサ熱"
  ],
  "2類感染症": [
    "急性灰白髄炎", "結核", "ジフテリア", "重症急性呼吸器症候群", 
    "中東呼吸器症候群", "鳥インフルエンザ（H5N1)", "鳥インフルエンザ（H7N9)",
    "インフルエンザ（H5N1）"
  ],
  "3類感染症": [
    "コレラ", "細菌性赤痢", "腸チフス", "パラチフス"
  ],
  "4類感染症": [
    "A型肝炎", "E型肝炎", "つつが虫病", "ウイルス性肝炎（Ｅ型肝炎及びＡ型肝炎を除く。）",
    "ウエストナイル熱", "エキノコックス症", "オウム病", "オムスク出血熱",
    "回帰熱", "Ｑ熱", "狂犬病", "コクシジオイデス症", "ジカウイルス感染症",
    "重症熱性血小板減少症候群", "腎症候性出血熱", "西部ウマ脳炎", "ダニ媒介脳炎",
    "炭疽", "チクングニア熱", "デング熱", "東部ウマ脳炎",
    "鳥インフルエンザ（H5N1およびH7N9を除く）", "鳥インフルエンザ（H5N1を除く）", 
    "鳥インフルエンザ", 
    "ニパウイルス感染症", "日本紅斑熱", "日本脳炎", "ハンタウイルス肺症候群", 
    "Ｂウイルス病", "鼻疽", "ブルセラ症", "ベネズエラウマ脳炎", 
    "ヘンドラウイルス感染症", "発しんチフス", "ボツリヌス症", "マラリア", 
    "野兎病", "ライム病", "リッサウイルス感染症", "リフトバレー熱",
    "類鼻疽", "レジオネラ症", "レプトスピラ症", "ロッキー山紅斑熱", "黄熱",
    "エムポックス", "キャサヌル森林病"
  ],
  "5類感染症": [
    "アメーバ赤痢", "ウイルス性肝炎（Ｅ型肝炎及びＡ型肝炎を除く。）", 
    "カルバペネム耐性腸内細菌目細菌感染症", "急性弛緩性麻痺（急性灰白髄炎を除く。）",
    "急性脳炎", "クリプトスポリジウム症", "クロイツフェルト・ヤコブ病", 
    "劇症型溶血性レンサ球菌感染症", "後天性免疫不全症候群", "ジアルジア症",
    "侵襲性インフルエンザ菌感染症", "侵襲性肺炎球菌感染症", "侵襲性髄膜炎菌感染症",
    "水痘（入院例に限る）", "先天性風しん症候群", "梅毒", "播種性クリプトコックス症",
    "バンコマイシン耐性腸球菌感染症", "バンコマイシン耐性黄色ブドウ球菌感染症",
    "百日咳", "風しん", "麻しん", "薬剤耐性アシネトバクター感染症", 
    "腸管出血性大腸菌感染症", "髄膜炎菌性髄膜炎", "破傷風", "乳児ボツリヌス症",
    "新型コロナウイルス感染症"
  ]
}

export default function DiseasesView({ dateRange }: DiseasesViewProps) {
  const [diseases, setDiseases] = useState<string[]>([])
  const [selectedDisease, setSelectedDisease] = useState<string>('')
  const [timeSeriesData, setTimeSeriesData] = useState<DiseaseTimeSeriesResponse | null>(null)
  const [startYear, setStartYear] = useState<number>(2020)
  const [endYear, setEndYear] = useState<number>(2024)
  const [isLoading, setIsLoading] = useState(true)
  const [isChartLoading, setIsChartLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [aggregationMode, setAggregationMode] = useState<'weekly' | 'monthly' | 'yearly'>('weekly')
  const [enableYearlyComparison, setEnableYearlyComparison] = useState<boolean>(false)
  const [selectedYears, setSelectedYears] = useState<number[]>([])
  const [yearlyData, setYearlyData] = useState<Record<number, DiseaseTimeSeriesResponse>>({})

  useEffect(() => {
    const fetchDiseases = async () => {
      try {
        setIsLoading(true)
        const data = await apiClient.getDiseases()
        setDiseases(data.diseases)
        if (data.diseases.length > 0) {
          setSelectedDisease(data.diseases[0])
        }
      } catch (error) {
        console.error('疾病リスト取得エラー:', error)
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
    } else {
      // デフォルト値: 過去5年間
      const currentYear = new Date().getFullYear()
      setStartYear(currentYear - 5)
      setEndYear(currentYear)
    }
    // 年毎比較が無効化されている場合は選択年をクリア
    if (!enableYearlyComparison) {
      setSelectedYears([])
    }
  }, [dateRange, enableYearlyComparison])

  useEffect(() => {
    if (selectedDisease) {
      fetchTimeSeriesData()
    }
  }, [selectedDisease, startYear, endYear, dateRange, aggregationMode, enableYearlyComparison, selectedYears])

  const fetchTimeSeriesData = async () => {
    if (!selectedDisease) return

    try {
      setIsChartLoading(true)
      const effectiveStartYear = dateRange ? dateRange.startYear : startYear
      const effectiveEndYear = dateRange ? dateRange.endYear : endYear
      
      // 年毎比較モード（週毎集計時のみ、かつ有効化されている場合）
      if (aggregationMode === 'weekly' && enableYearlyComparison && selectedYears.length > 0) {
        const yearlyDataMap: Record<number, DiseaseTimeSeriesResponse> = {}
        
        // 各年のデータを取得
        for (const year of selectedYears) {
          try {
            const data = await apiClient.getDiseaseTimeSeries(selectedDisease, year, year)
            if (data && data.data) {
              yearlyDataMap[year] = data
            }
          } catch (err) {
            console.warn(`${year}年のデータ取得に失敗:`, err)
          }
        }
        
        setYearlyData(yearlyDataMap)
        
        // 全体のデータも取得（後方互換性のため）
        const data = await apiClient.getDiseaseTimeSeries(selectedDisease, effectiveStartYear, effectiveEndYear)
        if (data && data.data) {
          setTimeSeriesData(data)
        } else {
          setTimeSeriesData(null)
        }
      } else {
        // 通常モード
        const data = await apiClient.getDiseaseTimeSeries(selectedDisease, effectiveStartYear, effectiveEndYear)
        if (data && data.data) {
          setTimeSeriesData(data)
        } else {
          setTimeSeriesData(null)
        }
        setYearlyData({})
      }
    } catch (error) {
      console.error('時系列データ取得エラー:', error)
      setTimeSeriesData(null)
      setYearlyData({})
    } finally {
      setIsChartLoading(false)
    }
  }

  // 疾病をカテゴリ別にグループ化
  const groupedDiseases = useMemo(() => {
    const grouped: Record<string, string[]> = {}
    const uncategorized: string[] = []

    // カテゴリ別にグループ化
    Object.keys(DISEASE_CATEGORIES).forEach(category => {
      grouped[category] = diseases.filter(disease => 
        DISEASE_CATEGORIES[category].includes(disease)
      ).sort()
    })

    // 分類に該当しない疾病
    diseases.forEach(disease => {
      const found = Object.values(DISEASE_CATEGORIES).some(categoryDiseases => 
        categoryDiseases.includes(disease)
      )
      if (!found) {
        uncategorized.push(disease)
      }
    })

    if (uncategorized.length > 0) {
      grouped['その他'] = uncategorized.sort()
    }

    return grouped
  }, [diseases])

  // フィルタリングされた疾病リスト
  const filteredDiseases = useMemo(() => {
    let result: string[] = []

    // カテゴリフィルタ
    if (selectedCategory === 'all') {
      result = diseases
    } else if (groupedDiseases[selectedCategory]) {
      result = groupedDiseases[selectedCategory]
    }

    // 検索フィルタ
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      result = result.filter(disease => 
        disease.toLowerCase().includes(query)
      )
    }

    return result
  }, [diseases, selectedCategory, searchQuery, groupedDiseases])

  // 週番号を計算する関数
  const getWeekNumber = (date: Date): number => {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
    const dayNum = d.getUTCDay() || 7
    d.setUTCDate(d.getUTCDate() + 4 - dayNum)
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
    return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
  }

  // 年毎比較用のチャートデータ準備
  const yearlyComparisonChartData = useMemo(() => {
    if (aggregationMode !== 'weekly' || !enableYearlyComparison || selectedYears.length === 0 || Object.keys(yearlyData).length === 0) {
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
        const date = new Date(item.date)
        const week = getWeekNumber(date)
        weekDataMap[week] = (weekDataMap[week] || 0) + item.value
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

  // データを集計する関数
  const aggregateData = useMemo(() => {
    if (!timeSeriesData || !timeSeriesData.data.length) return []

    const aggregated: Record<string, number> = {}

    timeSeriesData.data.forEach(item => {
      const date = new Date(item.date)
      let key: string

      switch (aggregationMode) {
        case 'monthly':
          key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
          break
        case 'yearly':
          key = String(date.getFullYear())
          break
        case 'weekly':
        default:
          key = item.date
          break
      }

      if (aggregated[key]) {
        aggregated[key] += item.value
      } else {
        aggregated[key] = item.value
      }
    })

    // ソートして配列に変換
    return Object.entries(aggregated)
      .map(([date, value]) => ({ date, value }))
      .sort((a, b) => a.date.localeCompare(b.date))
  }, [timeSeriesData, aggregationMode])

  // チャートデータの準備
  const chartData = useMemo(() => {
    // 年毎比較モードの場合
    if (yearlyComparisonChartData) {
      return yearlyComparisonChartData
    }

    // 通常モード
    if (!timeSeriesData || !aggregateData.length) {
      return { labels: [], datasets: [] }
    }

    return {
      labels: aggregateData.map(d => {
        if (aggregationMode === 'monthly') {
          const [year, month] = d.date.split('-')
          return `${year}年${parseInt(month)}月`
        } else if (aggregationMode === 'yearly') {
          return `${d.date}年`
        } else {
          return new Date(d.date).toLocaleDateString('ja-JP')
        }
      }),
      datasets: [
        {
          label: selectedDisease,
          data: aggregateData.map(d => d.value),
          borderColor: 'rgba(59, 130, 246, 1)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.1,
          fill: true,
        },
      ],
    }
  }, [timeSeriesData, aggregateData, aggregationMode, selectedDisease, yearlyComparisonChartData])

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: aggregationMode === 'weekly' && enableYearlyComparison && selectedYears.length > 1
          ? `${selectedDisease} の年毎比較（週毎）`
          : `${selectedDisease} の発生動向（${aggregationMode === 'weekly' ? '週毎' : aggregationMode === 'monthly' ? '月毎' : '年毎'}）`,
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
          text: aggregationMode === 'weekly' && enableYearlyComparison && selectedYears.length > 1 ? '週番号' : (aggregationMode === 'weekly' ? '報告日' : aggregationMode === 'monthly' ? '年月' : '年'),
        },
      },
    },
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">疾病別詳細分析</h2>
        <p className="text-gray-600 mb-6">
          個別の感染症について詳細な発生動向を分析できます。
        </p>

        {/* 疾病選択と検索 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              カテゴリ
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value)
                setSearchQuery('')
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">すべて</option>
              {Object.keys(groupedDiseases).map(category => (
                <option key={category} value={category}>
                  {category} ({groupedDiseases[category].length}件)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              検索
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="感染症名で検索..."
              className="w-full px-4 py-2 border border-gray-300 rounded-md text-gray-900 bg-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* 感染症選択 */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            感染症名
          </label>
          <select
            value={selectedDisease}
            onChange={(e) => setSelectedDisease(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {selectedCategory === 'all' ? (
              // カテゴリ別にグループ化して表示
              Object.keys(groupedDiseases).map(category => (
                <optgroup key={category} label={category}>
                  {groupedDiseases[category]
                    .filter(disease => !searchQuery.trim() || disease.toLowerCase().includes(searchQuery.toLowerCase()))
                    .map((disease) => (
                      <option key={disease} value={disease}>
                        {disease}
                      </option>
                    ))}
                </optgroup>
              ))
            ) : (
              // 選択されたカテゴリのみ表示
              filteredDiseases.map((disease) => (
                <option key={disease} value={disease}>
                  {disease}
                </option>
              ))
            )}
          </select>
          {filteredDiseases.length === 0 && searchQuery && (
            <p className="mt-1 text-sm text-gray-500">検索結果が見つかりませんでした</p>
          )}
        </div>

        {/* 集約モードと年毎比較 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
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
                  setEnableYearlyComparison(false)
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

          {/* 年毎比較トグル（週毎モード時のみ） */}
          {aggregationMode === 'weekly' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                年毎比較
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableYearlyComparison}
                  onChange={(e) => {
                    setEnableYearlyComparison(e.target.checked)
                    if (!e.target.checked) {
                      setYearlyData({})
                      setSelectedYears([])
                    } else {
                      // 有効化時にデフォルトで全ての年を選択
                      const years: number[] = []
                      for (let year = startYear; year <= endYear; year++) {
                        years.push(year)
                      }
                      setSelectedYears(years)
                    }
                  }}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-900">年毎比較を有効にする</span>
              </label>
            </div>
          )}
        </div>

        {/* 年毎比較設定（週毎モード時のみ、かつ有効化されている場合） */}
        {aggregationMode === 'weekly' && enableYearlyComparison && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              比較する年を選択（複数選択可）
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
      </div>

      {/* 統計情報 */}
      {aggregateData && aggregateData.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-sm text-gray-600">総報告数</div>
            <div className="text-2xl font-bold text-gray-900">
              {aggregateData.reduce((sum, d) => sum + d.value, 0).toLocaleString()}
            </div>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <div className="text-sm text-gray-600">最大値</div>
            <div className="text-2xl font-bold text-gray-900">
              {Math.max(...aggregateData.map(d => d.value)).toLocaleString()}
            </div>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4">
            <div className="text-sm text-gray-600">最小値</div>
            <div className="text-2xl font-bold text-gray-900">
              {Math.min(...aggregateData.map(d => d.value)).toLocaleString()}
            </div>
          </div>
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="text-sm text-gray-600">平均値</div>
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(aggregateData.reduce((sum, d) => sum + d.value, 0) / aggregateData.length).toLocaleString()}
            </div>
          </div>
        </div>
      )}

      {/* 時系列グラフ */}
      {isChartLoading ? (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <LoadingSpinner />
        </div>
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
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
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
                      {aggregationMode === 'monthly' ? (
                        (() => {
                          const [year, month] = item.date.split('-')
                          return `${year}年${parseInt(month)}月`
                        })()
                      ) : aggregationMode === 'yearly' ? (
                        `${item.date}年`
                      ) : (
                        item.date
                      )}
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
  )
}
