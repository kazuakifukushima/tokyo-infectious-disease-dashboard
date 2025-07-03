'use client'

import { useState, useEffect } from 'react'
import { Bar, Pie } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { apiClient } from '@/lib/api'
import LoadingSpinner from '../LoadingSpinner'
import type { CategoriesResponse } from '@/types'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

export default function CategoriesView() {
  const [categoriesData, setCategoriesData] = useState<CategoriesResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchCategoriesData = async () => {
      try {
        setIsLoading(true)
        const data = await apiClient.getCategories()
        setCategoriesData(data)
      } catch (error) {
        console.error('分類データ取得エラー:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchCategoriesData()
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!categoriesData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">データの取得に失敗しました</div>
      </div>
    )
  }

  const { categories } = categoriesData
  
  const reportCountChartData = {
    labels: categories.map(c => c.category),
    datasets: [
      {
        label: '総報告数',
        data: categories.map(c => c.total_count),
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(147, 51, 234, 0.8)',
          'rgba(156, 163, 175, 0.8)',
        ],
        borderWidth: 1,
      },
    ],
  }

  const diseaseCountChartData = {
    labels: categories.map(c => c.category),
    datasets: [
      {
        label: '疾病数',
        data: categories.map(c => c.disease_count),
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(147, 51, 234, 0.8)',
          'rgba(156, 163, 175, 0.8)',
        ],
        borderWidth: 1,
      },
    ],
  }

  const distributionChartData = {
    labels: categories.map(c => c.category),
    datasets: [
      {
        data: categories.map(c => c.total_count),
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

  const pieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
      },
    },
  }

  const totalReports = categories.reduce((sum, c) => sum + c.total_count, 0)
  const totalDiseaseTypes = categories.reduce((sum, c) => sum + c.disease_count, 0)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">法定感染症分類別統計</h2>
        <p className="text-gray-600">感染症法に基づく分類別の発生動向を分析できます。</p>
      </div>

      {/* サマリーカード */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="metric-card">
          <div className="text-sm opacity-90">総報告数</div>
          <div className="text-3xl font-bold">{totalReports.toLocaleString()}</div>
        </div>
        <div className="metric-card">
          <div className="text-sm opacity-90">総疾病種類数</div>
          <div className="text-3xl font-bold">{totalDiseaseTypes}</div>
        </div>
        <div className="metric-card">
          <div className="text-sm opacity-90">分類数</div>
          <div className="text-3xl font-bold">{categories.length}</div>
        </div>
      </div>

      {/* チャートセクション */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 分類別報告数 */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            分類別総報告数
          </h3>
          <div className="chart-container">
            <Bar data={reportCountChartData} options={chartOptions} />
          </div>
        </div>

        {/* 分類別疾病数 */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            分類別疾病種類数
          </h3>
          <div className="chart-container">
            <Bar data={diseaseCountChartData} options={chartOptions} />
          </div>
        </div>

        {/* 報告数分布 */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            報告数分布
          </h3>
          <div className="chart-container">
            <Pie data={distributionChartData} options={pieChartOptions} />
          </div>
        </div>

        {/* 詳細統計テーブル */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            分類別詳細統計
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3">分類</th>
                  <th className="text-right py-2 px-3">報告数</th>
                  <th className="text-right py-2 px-3">疾病数</th>
                  <th className="text-right py-2 px-3">構成比</th>
                </tr>
              </thead>
              <tbody>
                {categories
                  .sort((a, b) => b.total_count - a.total_count)
                  .map((category) => (
                    <tr key={category.category} className="border-b border-gray-100">
                      <td className="py-2 px-3 font-medium">
                        {category.category}
                      </td>
                      <td className="text-right py-2 px-3 font-mono">
                        {category.total_count.toLocaleString()}
                      </td>
                      <td className="text-right py-2 px-3 font-mono">
                        {category.disease_count}
                      </td>
                      <td className="text-right py-2 px-3 font-mono">
                        {((category.total_count / totalReports) * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 分類説明 */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          感染症法による分類について
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
          <div className="p-4 bg-red-50 rounded-lg">
            <h4 className="font-semibold text-red-800 mb-2">1類感染症</h4>
            <p className="text-red-700">
              感染力、罹患した場合の重篤性等から危険性が極めて高い感染症
            </p>
          </div>
          <div className="p-4 bg-orange-50 rounded-lg">
            <h4 className="font-semibold text-orange-800 mb-2">2類感染症</h4>
            <p className="text-orange-700">
              感染力、罹患した場合の重篤性等から危険性が高い感染症
            </p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg">
            <h4 className="font-semibold text-green-800 mb-2">3類感染症</h4>
            <p className="text-green-700">
              集団発生を起こし、特に飲食物を介して感染する可能性が高い感染症
            </p>
          </div>
          <div className="p-4 bg-blue-50 rounded-lg">
            <h4 className="font-semibold text-blue-800 mb-2">4類感染症</h4>
            <p className="text-blue-700">
              動物、飲食物等を介してヒトに感染する感染症
            </p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg">
            <h4 className="font-semibold text-purple-800 mb-2">5類感染症</h4>
            <p className="text-purple-700">
              国が感染症の発生動向の調査を行い、情報提供・公開していく感染症
            </p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-semibold text-gray-800 mb-2">その他</h4>
            <p className="text-gray-700">
              上記分類に該当しない感染症
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}