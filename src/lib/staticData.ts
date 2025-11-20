/**
 * 静的データファイルからデータを読み込むユーティリティ
 * Vercel環境でAPI接続に失敗した場合のフォールバックとして使用
 */

import type { SummaryData, DiseasesResponse } from '@/types'

let cachedSummaryData: SummaryData | null = null
let cachedDiseaseList: string[] | null = null
let cachedSentinelDiseaseList: string[] | null = null

/**
 * CSVファイルをパース（簡易版 - 引用符やエスケープを考慮）
 */
function parseCSV(csvText: string): any[] {
  const lines = csvText.split('\n').filter(line => line.trim())
  if (lines.length === 0) return []
  
  // ヘッダー行をパース
  const headers = parseCSVLine(lines[0])
  if (headers.length === 0) return []
  
  const data = []
  
  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i])
    if (values.length !== headers.length) {
      // カラム数が一致しない場合はスキップ
      continue
    }
    
    const row: any = {}
    headers.forEach((header, index) => {
      row[header] = values[index] || ''
    })
    data.push(row)
  }
  
  return data
}

/**
 * CSV行をパース（カンマ区切り、引用符を考慮）
 */
function parseCSVLine(line: string): string[] {
  const result: string[] = []
  let current = ''
  let inQuotes = false
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    
    if (char === '"') {
      inQuotes = !inQuotes
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  
  // 最後のフィールドを追加
  result.push(current.trim())
  
  return result
}

/**
 * 静的データファイルからサマリーデータを読み込む
 */
export async function loadStaticSummaryData(): Promise<SummaryData | null> {
  if (cachedSummaryData) {
    return cachedSummaryData
  }
  
  try {
    // Vercel環境では /data/ パスでアクセス可能
    const response = await fetch('/data/summary_statistics.json', {
      cache: 'no-cache'
    })
    if (!response.ok) {
      console.warn(`静的サマリーデータの読み込みに失敗しました: ${response.status} ${response.statusText}`)
      return null
    }
    cachedSummaryData = await response.json()
    return cachedSummaryData
  } catch (error) {
    console.error('静的サマリーデータの読み込みエラー:', error)
    return null
  }
}

/**
 * 静的データファイルから疾病リストを読み込む
 */
export async function loadStaticDiseaseList(): Promise<string[] | null> {
  if (cachedDiseaseList) {
    return cachedDiseaseList
  }
  
  try {
    const response = await fetch('/data/disease_list.json', {
      cache: 'no-cache'
    })
    if (!response.ok) {
      console.warn(`静的疾病リストの読み込みに失敗しました: ${response.status} ${response.statusText}`)
      return null
    }
    cachedDiseaseList = await response.json()
    return cachedDiseaseList
  } catch (error) {
    console.error('静的疾病リストの読み込みエラー:', error)
    return null
  }
}

/**
 * 静的データファイルから定点把握疾患リストを読み込む
 */
export async function loadStaticSentinelDiseaseList(): Promise<string[] | null> {
  if (cachedSentinelDiseaseList) {
    return cachedSentinelDiseaseList
  }
  
  try {
    const response = await fetch('/data/sentinel_disease_list.json', {
      cache: 'no-cache'
    })
    if (!response.ok) {
      console.warn(`静的定点把握疾患リストの読み込みに失敗しました: ${response.status} ${response.statusText}`)
      return null
    }
    cachedSentinelDiseaseList = await response.json()
    return cachedSentinelDiseaseList
  } catch (error) {
    console.error('静的定点把握疾患リストの読み込みエラー:', error)
    return null
  }
}

/**
 * 静的データファイルからCSVデータを読み込む
 */
export async function loadStaticCSVData(filename: string): Promise<any[] | null> {
  try {
    const response = await fetch(`/data/${filename}`, {
      cache: 'no-cache'
    })
    if (!response.ok) {
      console.warn(`静的CSVデータの読み込みに失敗しました: ${filename}`)
      return null
    }
    const csvText = await response.text()
    return parseCSV(csvText)
  } catch (error) {
    console.error(`静的CSVデータの読み込みエラー: ${filename}`, error)
    return null
  }
}

/**
 * 静的CSVデータから特定の疾病の時系列データを抽出
 */
export async function loadStaticDiseaseTimeSeries(
  diseaseName: string,
  startYear?: number,
  endYear?: number
): Promise<{ data: Array<{ date: string; value: number }> } | null> {
  try {
    console.log(`[loadStaticDiseaseTimeSeries] 開始: ${diseaseName}, ${startYear}-${endYear}`)
    const csvData = await loadStaticCSVData('infectious_diseases_data.csv')
    if (!csvData || csvData.length === 0) {
      console.warn('[loadStaticDiseaseTimeSeries] CSVデータが空です')
      return null
    }

    console.log(`[loadStaticDiseaseTimeSeries] CSVデータ読み込み完了: ${csvData.length}行`)
    
    // 疾病名でフィルタリング
    const filtered = csvData.filter((row: any) => {
      const rowDiseaseName = row['disease_name']
      return rowDiseaseName === diseaseName
    })

    console.log(`[loadStaticDiseaseTimeSeries] フィルタリング後: ${filtered.length}行`)

    if (filtered.length === 0) {
      console.warn(`[loadStaticDiseaseTimeSeries] 疾病名 "${diseaseName}" のデータが見つかりません`)
      return { data: [] }
    }

    // 日付と値を抽出
    const timeSeriesData = filtered
      .map((row: any) => {
        const dateStr = row['report_date']
        const valueStr = row['count']
        const year = parseInt(row['year'], 10)
        
        if (!dateStr || valueStr === undefined || valueStr === null || isNaN(year)) {
          return null
        }

        // 年でフィルタリング
        if (startYear && year < startYear) return null
        if (endYear && year > endYear) return null

        const value = parseInt(String(valueStr), 10)
        if (isNaN(value)) return null

        return {
          date: dateStr,
          value: value
        }
      })
      .filter((item): item is { date: string; value: number } => item !== null)
      .sort((a, b) => a.date.localeCompare(b.date))

    console.log(`[loadStaticDiseaseTimeSeries] 時系列データ抽出完了: ${timeSeriesData.length}件`)
    return { data: timeSeriesData }
  } catch (error) {
    console.error('[loadStaticDiseaseTimeSeries] エラー:', error)
    return null
  }
}

/**
 * 静的CSVデータから特定の定点把握疾患の時系列データを抽出
 */
export async function loadStaticSentinelDiseaseTimeSeries(
  diseaseName: string,
  startYear?: number,
  endYear?: number
): Promise<{ data: Array<{ date: string; value: number }> } | null> {
  try {
    const csvData = await loadStaticCSVData('sentinel_diseases_data.csv')
    if (!csvData || csvData.length === 0) {
      return null
    }

    // 疾病名でフィルタリング
    const filtered = csvData.filter((row: any) => {
      const rowDiseaseName = row['disease_name']
      return rowDiseaseName === diseaseName
    })

    if (filtered.length === 0) {
      return { data: [] }
    }

    // 日付と値を抽出
    const timeSeriesData = filtered
      .map((row: any) => {
        const dateStr = row['week_date'] || row['week']
        const valueStr = row['total_count']
        const year = parseInt(row['year'], 10)
        
        if (!dateStr || valueStr === undefined || valueStr === null || isNaN(year)) {
          return null
        }

        // 年でフィルタリング
        if (startYear && year < startYear) return null
        if (endYear && year > endYear) return null

        const value = parseInt(valueStr, 10)
        if (isNaN(value)) return null

        return {
          date: dateStr,
          value: value
        }
      })
      .filter((item): item is { date: string; value: number } => item !== null)
      .sort((a, b) => a.date.localeCompare(b.date))

    return { data: timeSeriesData }
  } catch (error) {
    console.error('静的定点把握疾患時系列データの読み込みエラー:', error)
    return null
  }
}

