import { format } from 'date-fns'
import { ja } from 'date-fns/locale'
import type { SummaryData } from '@/types'

interface HeaderProps {
  summaryData: SummaryData | null
}

export default function Header({ summaryData }: HeaderProps) {
  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'yyyy年M月d日', { locale: ja })
    } catch {
      return dateString
    }
  }

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            東京都感染症ダッシュボード
          </h1>
          {summaryData && (
            <p className="text-sm text-gray-600 mt-1">
              データ期間: {formatDate(summaryData.date_range.start)} ～ {formatDate(summaryData.date_range.end)}
            </p>
          )}
        </div>
        
        {summaryData && (
          <div className="flex items-center space-x-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">
                {summaryData.total_records.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">総レコード数</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">
                {summaryData.total_diseases}
              </div>
              <div className="text-xs text-gray-500">感染症種類</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">
                {summaryData.years_covered.length}
              </div>
              <div className="text-xs text-gray-500">対象年数</div>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}