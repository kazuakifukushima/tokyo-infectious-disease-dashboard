'use client'

import { useState, useEffect } from 'react'
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
import type { DiseasesResponse, DiseaseTimeSeriesResponse } from '@/types'

ChartJS.register(
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
)

export default function DiseasesView() {
  const [diseases, setDiseases] = useState<string[]>([])
  const [selectedDisease, setSelectedDisease] = useState<string>('')
  const [timeSeriesData, setTimeSeriesData] = useState<DiseaseTimeSeriesResponse | null>(null)
  const [startYear, setStartYear] = useState<number>(2020)
  const [endYear, setEndYear] = useState<number>(2024)
  const [isLoading, setIsLoading] = useState(true)
  const [isChartLoading, setIsChartLoading] = useState(false)

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
  }, [selectedDisease, startYear, endYear])

  const fetchTimeSeriesData = async () => {
    if (!selectedDisease) return

    try {
      setIsChartLoading(true)
      const data = await apiClient.getDiseaseTimeSeries(selectedDisease, startYear, endYear)
      setTimeSeriesData(data)
    } catch (error) {
      console.error('時系列データ取得エラー:', error)
      setTimeSeriesData(null)
    } finally {
      setIsChartLoading(false)
    }
  }

  const chartData = timeSeriesData ? {
    labels: timeSeriesData.data.map(d => new Date(d.date).toLocaleDateString('ja-JP')),
    datasets: [
      {
        label: selectedDisease,
        data: timeSeriesData.data.map(d => d.value),
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
        text: `${selectedDisease} の発生動向`,
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
          text: '報告日',
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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">感染症名</label>
            <select
              value={selectedDisease}
              onChange={(e) => setSelectedDisease(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {diseases.map((disease) => (
                <option key={disease} value={disease}>
                  {disease}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">開始年</label>
            <select
              value={startYear}
              onChange={(e) => setStartYear(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {Array.from({ length: 25 }, (_, i) => 2000 + i).map((year) => (
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {Array.from({ length: 25 }, (_, i) => 2000 + i).map((year) => (
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
              {timeSeriesData.total_records}
            </div>
            <div className="text-sm text-gray-600">データポイント数</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-green-600">
              {timeSeriesData.data.reduce((sum, d) => sum + d.value, 0)}
            </div>
            <div className="text-sm text-gray-600">期間内総報告数</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-orange-600">
              {Math.max(...timeSeriesData.data.map(d => d.value))}
            </div>
            <div className="text-sm text-gray-600">最大週間報告数</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-purple-600">
              {(timeSeriesData.data.reduce((sum, d) => sum + d.value, 0) / timeSeriesData.data.length).toFixed(1)}
            </div>
            <div className="text-sm text-gray-600">週平均報告数</div>
          </div>
        </div>
      )}

      {/* 時系列グラフ */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          時系列グラフ
        </h3>
        {isChartLoading ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        ) : timeSeriesData && timeSeriesData.data.length > 0 ? (
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
      {timeSeriesData && timeSeriesData.data.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            データ詳細 (最新20件)
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-4">報告日</th>
                  <th className="text-right py-2 px-4">報告数</th>
                </tr>
              </thead>
              <tbody>
                {timeSeriesData.data.slice(-20).reverse().map((item, index) => (
                  <tr key={index} className="border-b border-gray-100">
                    <td className="py-2 px-4">
                      {new Date(item.date).toLocaleDateString('ja-JP')}
                    </td>
                    <td className="text-right py-2 px-4 font-mono">
                      {item.value}
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