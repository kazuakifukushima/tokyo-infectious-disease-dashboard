'use client'

import { useState, useEffect } from 'react'
import OverviewView from './views/OverviewView'
import DiseasesView from './views/DiseasesView'
import TrendsView from './views/TrendsView'
import SentinelView from './views/SentinelView'
import type { ViewType, SummaryData, DateRange } from '@/types'

interface DashboardProps {
  activeView: ViewType
  summaryData: SummaryData | null
  dateRange: DateRange | null
}

export default function Dashboard({ activeView, summaryData, dateRange }: DashboardProps) {
  const renderView = () => {
    switch (activeView) {
      case 'overview':
        return <OverviewView summaryData={summaryData} dateRange={dateRange} />
      case 'diseases':
        return <DiseasesView dateRange={dateRange} />
      case 'trends':
        return <TrendsView dateRange={dateRange} />
      case 'sentinel':
        return <SentinelView dateRange={dateRange} />
      default:
        return <OverviewView summaryData={summaryData} dateRange={dateRange} />
    }
  }

  return (
    <div className="p-6">
      {renderView()}
    </div>
  )
}