'use client'

import { useState, useEffect } from 'react'

interface DateRange {
  startYear: number
  endYear: number
}

interface DateRangeSelectorProps {
  availableYears: number[]
  selectedRange: DateRange
  onRangeChange: (range: DateRange | null) => void
  isFiltered: boolean
}

export default function DateRangeSelector({ 
  availableYears, 
  selectedRange, 
  onRangeChange,
  isFiltered
}: DateRangeSelectorProps) {
  const [localStartYear, setLocalStartYear] = useState(selectedRange.startYear)
  const [localEndYear, setLocalEndYear] = useState(selectedRange.endYear)
  const [selectionMode, setSelectionMode] = useState<'range' | 'single'>(
    selectedRange.startYear === selectedRange.endYear ? 'single' : 'range'
  )

  useEffect(() => {
    setLocalStartYear(selectedRange.startYear)
    setLocalEndYear(selectedRange.endYear)
    setSelectionMode(selectedRange.startYear === selectedRange.endYear ? 'single' : 'range')
  }, [selectedRange])

  const handleStartYearChange = (year: number) => {
    const newStartYear = year
    const newEndYear = Math.max(newStartYear, localEndYear)
    setLocalStartYear(newStartYear)
    setLocalEndYear(newEndYear)
    onRangeChange({
      startYear: newStartYear,
      endYear: newEndYear
    })
  }

  const handleEndYearChange = (year: number) => {
    const newEndYear = year
    const newStartYear = Math.min(localStartYear, newEndYear)
    setLocalStartYear(newStartYear)
    setLocalEndYear(newEndYear)
    onRangeChange({
      startYear: newStartYear,
      endYear: newEndYear
    })
  }

  const handleSingleYearChange = (year: number) => {
    setLocalStartYear(year)
    setLocalEndYear(year)
    onRangeChange({
      startYear: year,
      endYear: year
    })
  }

  const handlePresetSelect = (preset: 'all' | 'last3' | 'last5' | 'current') => {
    const currentYear = new Date().getFullYear()
    let startYear: number
    let endYear: number

    const minYear = availableYears.length > 0 ? Math.min(...availableYears) : currentYear
    const maxYear = availableYears.length > 0 ? Math.max(...availableYears) : currentYear

    switch (preset) {
      case 'all':
        startYear = minYear
        endYear = maxYear
        break
      case 'last3':
        startYear = Math.max(currentYear - 3, minYear)
        // 現在年と利用可能な最大年の小さい方を使用（データが存在しない現在年を選択しないように）
        endYear = Math.min(currentYear, maxYear)
        break
      case 'last5':
        startYear = Math.max(currentYear - 5, minYear)
        // 現在年と利用可能な最大年の小さい方を使用（データが存在しない現在年を選択しないように）
        endYear = Math.min(currentYear, maxYear)
        break
      case 'current':
        startYear = maxYear
        endYear = maxYear
        break
      default:
        return
    }

    setLocalStartYear(startYear)
    setLocalEndYear(endYear)
    setSelectionMode(startYear === endYear ? 'single' : 'range')
    onRangeChange({ startYear, endYear })
  }

  const minYear = availableYears.length > 0 ? Math.min(...availableYears) : new Date().getFullYear()
  const maxYear = availableYears.length > 0 ? Math.max(...availableYears) : new Date().getFullYear()
  const isSingleYear = localStartYear === localEndYear

  return (
    <div className="flex items-center space-x-4 flex-wrap gap-y-2">
      {/* プリセットボタン */}
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-600">クイック選択:</span>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => handlePresetSelect('all')}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              !isFiltered || (localStartYear === minYear && localEndYear === maxYear)
                ? 'bg-primary-600 text-white font-medium'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            全期間
          </button>
          <button
            onClick={() => handlePresetSelect('last5')}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              isFiltered && localStartYear === Math.max(new Date().getFullYear() - 5, minYear) && localEndYear === Math.min(new Date().getFullYear(), maxYear)
                ? 'bg-primary-600 text-white font-medium'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            過去5年
          </button>
          <button
            onClick={() => handlePresetSelect('last3')}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              isFiltered && localStartYear === Math.max(new Date().getFullYear() - 3, minYear) && localEndYear === Math.min(new Date().getFullYear(), maxYear)
                ? 'bg-primary-600 text-white font-medium'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            過去3年
          </button>
          <button
            onClick={() => handlePresetSelect('current')}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              isFiltered && localStartYear === maxYear && localEndYear === maxYear
                ? 'bg-primary-600 text-white font-medium'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            今年
          </button>
        </div>
      </div>

      {/* 単年選択 */}
      <div className="flex items-center space-x-2 border-l border-gray-300 pl-4">
        <span className="text-sm text-gray-600">単年:</span>
        <select
          value={isSingleYear ? localStartYear : ''}
          onChange={(e) => {
            const year = Number(e.target.value)
            handleSingleYearChange(year)
            setSelectionMode('single')
          }}
          className={`px-3 py-1.5 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors ${
            isFiltered && isSingleYear
              ? 'bg-blue-50 border-blue-300 text-blue-700'
              : 'bg-white border-gray-300 text-gray-700'
          }`}
        >
          <option value="">選択してください</option>
          {availableYears.map(year => (
            <option key={year} value={year}>{year}年</option>
          ))}
        </select>
      </div>

      {/* 期間選択 */}
      <div className="flex items-center space-x-2 border-l border-gray-300 pl-4">
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setSelectionMode('range')}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              selectionMode === 'range'
                ? 'bg-primary-100 text-primary-700 font-medium'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            期間
          </button>
          <span className="text-gray-300">|</span>
          <button
            onClick={() => {
              setSelectionMode('single')
              if (localStartYear !== localEndYear) {
                handleSingleYearChange(localStartYear)
              }
            }}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              selectionMode === 'single'
                ? 'bg-primary-100 text-primary-700 font-medium'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            単年
          </button>
        </div>
        {selectionMode === 'range' ? (
          <div className="flex items-center space-x-2">
            <select
              value={localStartYear}
              onChange={(e) => handleStartYearChange(Number(e.target.value))}
              className={`px-3 py-1.5 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors ${
                isFiltered
                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700'
              }`}
            >
              {availableYears.map(year => (
                <option key={year} value={year}>{year}年</option>
              ))}
            </select>
            <span className="text-sm text-gray-500">～</span>
            <select
              value={localEndYear}
              onChange={(e) => handleEndYearChange(Number(e.target.value))}
              className={`px-3 py-1.5 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors ${
                isFiltered
                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700'
              }`}
            >
              {availableYears.map(year => (
                <option key={year} value={year}>{year}年</option>
              ))}
            </select>
          </div>
        ) : (
          <select
            value={localStartYear}
            onChange={(e) => handleSingleYearChange(Number(e.target.value))}
            className={`px-3 py-1.5 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors ${
              isFiltered
                ? 'bg-blue-50 border-blue-300 text-blue-700'
                : 'bg-white border-gray-300 text-gray-700'
            }`}
          >
            {availableYears.map(year => (
              <option key={year} value={year}>{year}年</option>
            ))}
          </select>
        )}
      </div>

      {/* フィルター解除ボタン */}
      {isFiltered && (
        <button
          onClick={() => onRangeChange(null)}
          className="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md border border-red-200 hover:border-red-300 transition-colors"
          title="フィルターを解除"
        >
          <span className="flex items-center space-x-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span>リセット</span>
          </span>
        </button>
      )}
    </div>
  )
} 