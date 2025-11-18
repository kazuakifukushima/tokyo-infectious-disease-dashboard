'use client'

import { useState, useEffect } from 'react'
import Dashboard from '@/components/Dashboard'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import LoadingSpinner from '@/components/LoadingSpinner'
import DateRangeSelector from '@/components/DateRangeSelector'
import { apiClient } from '@/lib/api'
import type { SummaryData, DateRange } from '@/types'

export default function Home() {
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<'overview' | 'diseases' | 'trends' | 'sentinel'>('overview')
  const [dateRange, setDateRange] = useState<DateRange | null>(null)

  useEffect(() => {
    const fetchSummaryData = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const data = await apiClient.getSummary(dateRange || undefined)
        if (data) {
          setSummaryData(data)
          setError(null)
        } else {
          setError('データが見つかりませんでした')
        }
      } catch (err: any) {
        console.error('データ取得エラー:', err)
        // エラーメッセージをより詳細に
        const errorMessage = err?.message || 'データの取得に失敗しました'
        setError(errorMessage)
      } finally {
        setIsLoading(false)
      }
    }

    fetchSummaryData()
  }, [dateRange])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="card max-w-md">
          <div className="text-center">
            <div className="text-red-500 text-xl mb-2">エラー</div>
            <p className="text-gray-600">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-4 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
            >
              再読み込み
            </button>
          </div>
        </div>
      </div>
    )
  }

  const handleDateRangeChange = (range: DateRange | null) => {
    setDateRange(range)
  }

  const availableYears = summaryData?.years_covered || []
  const defaultStartYear = availableYears.length > 0 ? Math.min(...availableYears) : new Date().getFullYear()
  const defaultEndYear = availableYears.length > 0 ? Math.max(...availableYears) : new Date().getFullYear()

  return (
    <div className="flex h-screen">
      <Sidebar activeView={activeView} onViewChange={setActiveView} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header summaryData={summaryData} />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
          <div className="p-4 border-b border-gray-200 bg-white">
            <div className="flex items-center space-x-4">
              <h2 className="text-lg font-semibold text-gray-900">データ期間</h2>
              <DateRangeSelector
                availableYears={availableYears}
                selectedRange={dateRange || { startYear: defaultStartYear, endYear: defaultEndYear }}
                onRangeChange={handleDateRangeChange}
                isFiltered={dateRange !== null}
              />
            </div>
          </div>
          <Dashboard activeView={activeView} summaryData={summaryData} dateRange={dateRange} />
        </main>
      </div>
    </div>
  )
}