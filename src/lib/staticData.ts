/**
 * 静的データファイルからデータを読み込むユーティリティ
 * Vercel環境でAPI接続に失敗した場合のフォールバックとして使用
 */

import type { SummaryData, DiseasesResponse } from '@/types'

let cachedSummaryData: SummaryData | null = null
let cachedDiseaseList: string[] | null = null
let cachedSentinelDiseaseList: string[] | null = null

/**
 * CSVファイルをパース
 */
function parseCSV(csvText: string): any[] {
  const lines = csvText.split('\n').filter(line => line.trim())
  if (lines.length === 0) return []
  
  const headers = lines[0].split(',').map(h => h.trim())
  const data = []
  
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim())
    const row: any = {}
    headers.forEach((header, index) => {
      row[header] = values[index] || ''
    })
    data.push(row)
  }
  
  return data
}

/**
 * 静的データファイルからサマリーデータを読み込む
 */
export async function loadStaticSummaryData(): Promise<SummaryData | null> {
  if (cachedSummaryData) {
    return cachedSummaryData
  }
  
  try {
    const response = await fetch('/data/summary_statistics.json')
    if (!response.ok) {
      console.warn('静的サマリーデータの読み込みに失敗しました')
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
    const response = await fetch('/data/disease_list.json')
    if (!response.ok) {
      console.warn('静的疾病リストの読み込みに失敗しました')
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
    const response = await fetch('/data/sentinel_disease_list.json')
    if (!response.ok) {
      console.warn('静的定点把握疾患リストの読み込みに失敗しました')
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
    const response = await fetch(`/data/${filename}`)
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

