'use client'

import { useState, useEffect } from 'react'
import { Bar, Line, Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { apiClient } from '@/lib/api'
import LoadingSpinner from '../LoadingSpinner'
import type { SummaryData, TopDiseasesResponse, YearlyTrendsResponse } from '@/types'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

interface OverviewViewProps {
  summaryData: SummaryData | null
}

export default function OverviewView({ summaryData }: OverviewViewProps) {
  const [topDiseases, setTopDiseases] = useState<TopDiseasesResponse | null>(null)
  const [yearlyTrends, setYearlyTrends] = useState<YearlyTrendsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true)
        const [topDiseasesData, yearlyTrendsData] = await Promise.all([
          apiClient.getTopDiseases(10),
          apiClient.getYearlyTrends()
        ])
        setTopDiseases(topDiseasesData)
        setYearlyTrends(yearlyTrendsData)
      } catch (error) {
        console.error('データ取得エラー:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const topDiseasesChartData = {
    labels: topDiseases?.top_diseases.map(d => d.disease_name) || [],
    datasets: [
      {
        label: '報告数',
        data: topDiseases?.top_diseases.map(d => d.total_count) || [],
        backgroundColor: 'rgba(59, 130, 246, 0.6)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
      },
    ],
  }

  const yearlyTrendsChartData = {
    labels: yearlyTrends?.yearly_trends.map(t => t.year.toString()) || [],
    datasets: [
      {
        label: '年間総報告数',
        data: yearlyTrends?.yearly_trends.map(t => t.total_count) || [],
        borderColor: 'rgba(34, 197, 94, 1)',
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        tension: 0.1,
      },
    ],
  }

  const categoryData = summaryData?.disease_categories || {}
  const categoryChartData = {
    labels: Object.keys(categoryData),
    datasets: [
      {
        data: Object.values(categoryData),
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(147, 51, 234, 0.8)',
          'rgba(156, 163, 175, 0.8)',
        ],
        borderWidth: 2,
      },
    ],
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">感染症発生動向 概況</h2>
        <p className="text-gray-600">東京都における感染症の全体的な発生状況をご覧いただけます。</p>
      </div>

      {/* サマリーカード */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="metric-card">
          <div className="text-sm opacity-90">総レコード数</div>
          <div className="text-3xl font-bold">
            {summaryData?.total_records.toLocaleString() || 0}
          </div>
        </div>
        <div className="metric-card">
          <div className="text-sm opacity-90">感染症種類</div>
          <div className="text-3xl font-bold">
            {summaryData?.total_diseases || 0}
          </div>
        </div>
        <div className="metric-card">
          <div className="text-sm opacity-90">対象年数</div>
          <div className="text-3xl font-bold">
            {summaryData?.years_covered.length || 0}
          </div>
        </div>
        <div className="metric-card">
          <div className="text-sm opacity-90">法定分類数</div>
          <div className="text-3xl font-bold">
            {Object.keys(summaryData?.disease_categories || {}).length}
          </div>
        </div>
      </div>

      {/* チャートセクション */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 上位感染症 */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            報告数上位感染症 (全期間)
          </h3>
          <div className="chart-container">
            <Bar data={topDiseasesChartData} options={chartOptions} />
          </div>
        </div>

        {/* 年次推移 */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            年次感染症報告数推移
          </h3>
          <div className="chart-container">
            <Line data={yearlyTrendsChartData} options={chartOptions} />
          </div>
        </div>

        {/* 法定分類別分布 */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            法定分類別感染症分布
          </h3>
          <div className="chart-container">
            <Doughnut 
              data={categoryChartData} 
              options={{
                ...chartOptions,
                plugins: {
                  ...chartOptions.plugins,
                  legend: {
                    position: 'right' as const,
                  },
                },
              }} 
            />
          </div>
        </div>

        {/* 統計情報 */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            データ統計情報
          </h3>
          <div className="space-y-4">
            {summaryData && (
              <>
                <div className="flex justify-between">
                  <span className="text-gray-600">データ期間:</span>
                  <span className="font-medium">
                    {new Date(summaryData.date_range.start).getFullYear()} - {new Date(summaryData.date_range.end).getFullYear()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">最新年度総報告数:</span>
                  <span className="font-medium">
                    {Object.values(summaryData.yearly_totals).slice(-1)[0]?.toLocaleString() || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">最多報告感染症:</span>
                  <span className="font-medium">
                    {Object.keys(summaryData.top_diseases)[0] || '-'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">最多報告数:</span>
                  <span className="font-medium">
                    {Object.values(summaryData.top_diseases)[0]?.toLocaleString() || 0}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}