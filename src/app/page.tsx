'use client'

import { useState, useEffect } from 'react'
import Dashboard from '@/components/Dashboard'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import LoadingSpinner from '@/components/LoadingSpinner'
import { apiClient } from '@/lib/api'
import type { SummaryData } from '@/types'

export default function Home() {
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<'overview' | 'diseases' | 'categories' | 'trends'>('overview')

  useEffect(() => {
    const fetchSummaryData = async () => {
      try {
        setIsLoading(true)
        const data = await apiClient.getSummary()
        setSummaryData(data)
        setError(null)
      } catch (err) {
        console.error('データ取得エラー:', err)
        setError('データの取得に失敗しました')
      } finally {
        setIsLoading(false)
      }
    }

    fetchSummaryData()
  }, [])

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

  return (
    <div className="flex h-screen">
      <Sidebar activeView={activeView} onViewChange={setActiveView} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header summaryData={summaryData} />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
          <Dashboard activeView={activeView} summaryData={summaryData} />
        </main>
      </div>
    </div>
  )
}