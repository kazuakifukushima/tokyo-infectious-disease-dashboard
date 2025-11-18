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
import type { DiseasesResponse, DiseaseTimeSeriesResponse, DateRange } from '@/types'

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

// 感染症の法定分類定義
const DISEASE_CATEGORIES: Record<string, string[]> = {
  "1類感染症": [
    "エボラ出血熱", "クリミア・コンゴ出血熱", "痘そう", "南米出血熱", 
    "ペスト", "マールブルグ病", "ラッサ熱"
  ],
  "2類感染症": [
    "急性灰白髄炎", "結核", "ジフテリア", "重症急性呼吸器症候群", 
    "中東呼吸器症候群", "鳥インフルエンザ（H5N1)", "鳥インフルエンザ（H7N9)"
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
    "鳥インフルエンザ（H5N1およびH7N9を除く）", "ニパウイルス感染症", "日本紅斑熱", 
    "日本脳炎", "ハンタウイルス肺症候群", "Ｂウイルス病", "鼻疽", "ブルセラ症",
    "ベネズエラウマ脳炎", "ヘンドラウイルス感染症", "発しんチフス", "ボツリヌス症",
    "マラリア", "野兎病", "ライム病", "リッサウイルス感染症", "リフトバレー熱",
    "類鼻疽", "レジオネラ症", "レプトスピラ症", "ロッキー山紅斑熱", "黄熱"
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
    "腸管出血性大腸菌感染症", "髄膜炎菌性髄膜炎"
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
    if (selectedDisease) {
      fetchTimeSeriesData()
    }
  }, [selectedDisease, startYear, endYear, dateRange])

  const fetchTimeSeriesData = async () => {
    if (!selectedDisease) return

    try {
      setIsChartLoading(true)
      const effectiveStartYear = dateRange ? dateRange.startYear : startYear
      const effectiveEndYear = dateRange ? dateRange.endYear : endYear
      const data = await apiClient.getDiseaseTimeSeries(selectedDisease, effectiveStartYear, effectiveEndYear)
      setTimeSeriesData(data)
    } catch (error) {
      console.error('時系列データ取得エラー:', error)
      setTimeSeriesData(null)
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

  const chartData = timeSeriesData && aggregateData.length > 0 ? {
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
  } : { labels: [], datasets: [] }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `${selectedDisease} の発生動向 (${aggregationMode === 'weekly' ? '週毎' : aggregationMode === 'monthly' ? '月毎' : '年毎'})`,
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
          text: aggregationMode === 'weekly' ? '報告日' : aggregationMode === 'monthly' ? '年月' : '年',
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
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">疾病別詳細分析</h2>
        <p className="text-gray-600">個別の感染症について詳細な発生動向を分析できます。</p>
      </div>

      {/* 検索・フィルタセクション */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">分析対象設定</h3>
        
        {/* カテゴリ選択と検索 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">カテゴリ</label>
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value)
                setSearchQuery('')
              }}
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
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
            <label className="block text-sm font-medium text-gray-700 mb-1">検索</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="感染症名で検索..."
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        {/* 感染症選択 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">感染症名</label>
          <select
            value={selectedDisease}
            onChange={(e) => setSelectedDisease(e.target.value)}
            className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
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

        {/* 期間選択 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">開始年</label>
            <select
              value={startYear}
              onChange={(e) => setStartYear(Number(e.target.value))}
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {Array.from({ length: 26 }, (_, i) => 2000 + i).map((year) => (
                <option key={year} value={year}>
                  {year}年
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">終了年</label>
            <select
              value={endYear}
              onChange={(e) => setEndYear(Number(e.target.value))}
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {Array.from({ length: 26 }, (_, i) => 2000 + i).map((year) => (
                <option key={year} value={year}>
                  {year}年
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={fetchTimeSeriesData}
              disabled={isChartLoading}
              className="w-full px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isChartLoading ? '読み込み中...' : '更新'}
            </button>
          </div>
        </div>
      </div>

      {/* 統計サマリー */}
      {timeSeriesData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card text-center">
            <div className="text-2xl font-bold text-primary-600">
              {aggregateData.length}
            </div>
            <div className="text-sm text-gray-600">
              {aggregationMode === 'weekly' ? 'データポイント数' : aggregationMode === 'monthly' ? '月数' : '年数'}
            </div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-green-600">
              {aggregateData.reduce((sum, d) => sum + d.value, 0)}
            </div>
            <div className="text-sm text-gray-600">期間内総報告数</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-orange-600">
              {aggregateData.length > 0 ? Math.max(...aggregateData.map(d => d.value)) : 0}
            </div>
            <div className="text-sm text-gray-600">
              {aggregationMode === 'weekly' ? '最大週間報告数' : aggregationMode === 'monthly' ? '最大月間報告数' : '最大年間報告数'}
            </div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-purple-600">
              {aggregateData.length > 0 ? (aggregateData.reduce((sum, d) => sum + d.value, 0) / aggregateData.length).toFixed(1) : 0}
            </div>
            <div className="text-sm text-gray-600">
              {aggregationMode === 'weekly' ? '週平均報告数' : aggregationMode === 'monthly' ? '月平均報告数' : '年平均報告数'}
            </div>
          </div>
        </div>
      )}

      {/* 時系列グラフ */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            時系列グラフ
          </h3>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">集計単位:</span>
            <select
              value={aggregationMode}
              onChange={(e) => setAggregationMode(e.target.value as 'weekly' | 'monthly' | 'yearly')}
              className="px-3 py-1.5 bg-white border border-gray-300 rounded-md text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="weekly">週毎</option>
              <option value="monthly">月毎</option>
              <option value="yearly">年毎</option>
            </select>
          </div>
        </div>
        {isChartLoading ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        ) : timeSeriesData && aggregateData.length > 0 ? (
          <div style={{ height: '400px' }}>
            <Line data={chartData} options={chartOptions} />
          </div>
        ) : (
          <div className="flex items-center justify-center h-64 text-gray-500">
            データがありません
          </div>
        )}
      </div>

      {/* データテーブル */}
      {timeSeriesData && aggregateData.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            データ詳細 (最新20件)
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-2 px-4 font-medium text-gray-700">
                    {aggregationMode === 'weekly' ? '報告日' : aggregationMode === 'monthly' ? '年月' : '年'}
                  </th>
                  <th className="text-right py-2 px-4 font-medium text-gray-700">報告数</th>
                </tr>
              </thead>
              <tbody>
                {aggregateData.slice(-20).reverse().map((item, index) => (
                  <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-2 px-4 text-gray-900">
                      {aggregationMode === 'monthly' ? (
                        (() => {
                          const [year, month] = item.date.split('-')
                          return `${year}年${parseInt(month)}月`
                        })()
                      ) : aggregationMode === 'yearly' ? (
                        `${item.date}年`
                      ) : (
                        new Date(item.date).toLocaleDateString('ja-JP')
                      )}
                    </td>
                    <td className="text-right py-2 px-4 font-mono text-gray-900">
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
