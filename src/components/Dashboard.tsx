'use client'

import { useState, useEffect } from 'react'
import OverviewView from './views/OverviewView'
import DiseasesView from './views/DiseasesView'
import CategoriesView from './views/CategoriesView'
import TrendsView from './views/TrendsView'
import type { ViewType, SummaryData } from '@/types'

interface DashboardProps {
  activeView: ViewType
  summaryData: SummaryData | null
}

export default function Dashboard({ activeView, summaryData }: DashboardProps) {
  const renderView = () => {
    switch (activeView) {
      case 'overview':
        return <OverviewView summaryData={summaryData} />
      case 'diseases':
        return <DiseasesView />
      case 'categories':
        return <CategoriesView />
      case 'trends':
        return <TrendsView />
      default:
        return <OverviewView summaryData={summaryData} />
    }
  }

  return (
    <div className="p-6">
      {renderView()}
    </div>
  )
}