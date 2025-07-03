'use client'

import { useState, useEffect } from 'react'
import { Line, Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { apiClient } from '@/lib/api'
import LoadingSpinner from '../LoadingSpinner'
import type { YearlyTrendsResponse, TopDiseasesResponse } from '@/types'

ChartJS.register(
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

export default function TrendsView() {
  const [yearlyTrends, setYearlyTrends] = useState<YearlyTrendsResponse | null>(null)
  const [recentTrends, setRecentTrends] = useState<TopDiseasesResponse | null>(null)
  const [selectedYear, setSelectedYear] = useState<number>(2024)
  const [isLoading, setIsLoading] = useState(true)
  const [isYearDataLoading, setIsYearDataLoading] = useState(false)

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setIsLoading(true)
        const [trendsData, recentData] = await Promise.all([
          apiClient.getYearlyTrends(),
          apiClient.getTopDiseases(10, 2024)
        ])
        setYearlyTrends(trendsData)
        setRecentTrends(recentData)
      } catch (error) {
        console.error('データ取得エラー:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchInitialData()
  }, [])

  useEffect(() => {
    if (selectedYear) {
      fetchYearData()
    }
  }, [selectedYear])

  const fetchYearData = async () => {
    try {
      setIsYearDataLoading(true)
      const data = await apiClient.getTopDiseases(10, selectedYear)
      setRecentTrends(data)
    } catch (error) {
      console.error('年別データ取得エラー:', error)
    } finally {
      setIsYearDataLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const yearlyChartData = yearlyTrends ? {
    labels: yearlyTrends.yearly_trends.map(t => t.year.toString()),
    datasets: [
      {
        label: '年間総報告数',
        data: yearlyTrends.yearly_trends.map(t => t.total_count),
        borderColor: 'rgba(59, 130, 246, 1)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1,
        fill: true,
      },
    ],
  } : { labels: [], datasets: [] }

  const yearlyBarChartData = recentTrends ? {
    labels: recentTrends.top_diseases.map(d => d.disease_name),
    datasets: [
      {
        label: `${selectedYear}年 報告数`,
        data: recentTrends.top_diseases.map(d => d.total_count),
        backgroundColor: 'rgba(34, 197, 94, 0.6)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 1,
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
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: '報告数',
        },
      },
    },
  }

  const availableYears = yearlyTrends?.yearly_trends.map(t => t.year) || []
  const averageReports = yearlyTrends ? 
    Math.round(yearlyTrends.yearly_trends.reduce((sum, t) => sum + t.total_count, 0) / yearlyTrends.yearly_trends.length) : 0
  
  const maxYear = yearlyTrends?.yearly_trends.reduce((max, t) => t.total_count > max.total_count ? t : max)
  const minYear = yearlyTrends?.yearly_trends.reduce((min, t) => t.total_count < min.total_count ? t : min)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">長期時系列分析</h2>
        <p className="text-gray-600">感染症の長期的な発生動向とトレンドを分析できます。</p>
      </div>

      {/* 統計サマリー */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="metric-card">
          <div className="text-sm opacity-90">年平均報告数</div>
          <div className="text-3xl font-bold">{averageReports.toLocaleString()}</div>
        </div>
        <div className="metric-card">
          <div className="text-sm opacity-90">最多報告年</div>
          <div className="text-3xl font-bold">{maxYear?.year || '-'}</div>
          <div className="text-sm opacity-75">{maxYear?.total_count.toLocaleString() || 0}</div>
        </div>
        <div className="metric-card">
          <div className="text-sm opacity-90">最少報告年</div>
          <div className="text-3xl font-bold">{minYear?.year || '-'}</div>
          <div className="text-sm opacity-75">{minYear?.total_count.toLocaleString() || 0}</div>
        </div>
        <div className="metric-card">
          <div className="text-sm opacity-90">対象期間</div>
          <div className="text-3xl font-bold">{availableYears.length}</div>
          <div className="text-sm opacity-75">年間</div>
        </div>
      </div>

      {/* 年次推移グラフ */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          年次感染症報告数推移 ({availableYears[0]} - {availableYears[availableYears.length - 1]})
        </h3>
        <div style={{ height: '400px' }}>
          <Line data={yearlyChartData} options={chartOptions} />
        </div>
      </div>

      {/* 年別詳細分析 */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            年別上位感染症
          </h3>
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">対象年:</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {availableYears.map((year) => (
                <option key={year} value={year}>
                  {year}年
                </option>
              ))}
            </select>
          </div>
        </div>
        
        {isYearDataLoading ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <div style={{ height: '400px' }}>
            <Bar data={yearlyBarChartData} options={chartOptions} />
          </div>
        )}
      </div>

      {/* トレンド分析テーブル */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            年次統計データ
          </h3>
          <div className="overflow-x-auto max-h-64 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3">年</th>
                  <th className="text-right py-2 px-3">報告数</th>
                  <th className="text-right py-2 px-3">前年比</th>
                </tr>
              </thead>
              <tbody>
                {yearlyTrends?.yearly_trends.slice().reverse().map((trend, index, array) => {
                  const previousYear = array[index + 1]
                  const changePercent = previousYear ? 
                    ((trend.total_count - previousYear.total_count) / previousYear.total_count * 100) : null
                  
                  return (
                    <tr key={trend.year} className="border-b border-gray-100">
                      <td className="py-2 px-3 font-medium">{trend.year}年</td>
                      <td className="text-right py-2 px-3 font-mono">
                        {trend.total_count.toLocaleString()}
                      </td>
                      <td className={`text-right py-2 px-3 font-mono ${
                        changePercent === null ? 'text-gray-400' :
                        changePercent > 0 ? 'text-red-600' : 'text-green-600'
                      }`}>
                        {changePercent === null ? '-' : 
                         `${changePercent > 0 ? '+' : ''}${changePercent.toFixed(1)}%`}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {selectedYear}年 上位疾病詳細
          </h3>
          {isYearDataLoading ? (
            <div className="flex items-center justify-center h-32">
              <LoadingSpinner />
            </div>
          ) : recentTrends ? (
            <div className="overflow-x-auto max-h-64 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-white">
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-3">順位</th>
                    <th className="text-left py-2 px-3">感染症名</th>
                    <th className="text-right py-2 px-3">報告数</th>
                    <th className="text-left py-2 px-3">分類</th>
                  </tr>
                </thead>
                <tbody>
                  {recentTrends.top_diseases.map((disease, index) => (
                    <tr key={disease.disease_name} className="border-b border-gray-100">
                      <td className="py-2 px-3 font-medium">{index + 1}</td>
                      <td className="py-2 px-3">{disease.disease_name}</td>
                      <td className="text-right py-2 px-3 font-mono">
                        {disease.total_count.toLocaleString()}
                      </td>
                      <td className="py-2 px-3 text-xs">
                        <span className="px-2 py-1 bg-gray-100 rounded">
                          {disease.category}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              データがありません
            </div>
          )}
        </div>
      </div>
    </div>
  )
}