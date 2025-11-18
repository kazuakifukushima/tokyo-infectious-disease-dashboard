import { clsx } from 'clsx'
import type { ViewType } from '@/types'

interface SidebarProps {
  activeView: ViewType
  onViewChange: (view: ViewType) => void
}

const navigationItems = [
  {
    id: 'overview' as ViewType,
    name: '概況',
    icon: '📊',
    description: '全体的な発生動向'
  },
  {
    id: 'trends' as ViewType,
    name: '時系列分析',
    icon: '📈',
    description: '長期トレンド分析'
  },
  {
    id: 'diseases' as ViewType,
    name: '疾病別分析',
    icon: '🦠',
    description: '個別疾病の詳細'
  },
  {
    id: 'sentinel' as ViewType,
    name: '定点把握疾患',
    icon: '🏥',
    description: 'インフルエンザ・COVID-19等'
  }
]

export default function Sidebar({ activeView, onViewChange }: SidebarProps) {
  return (
    <aside className="sidebar w-64 h-full flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <div className="text-2xl">🏥</div>
          <div>
            <h2 className="font-semibold text-gray-900">IDSC Dashboard</h2>
            <p className="text-xs text-gray-500">感染症データ分析</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navigationItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onViewChange(item.id)}
                className={clsx(
                  'nav-item w-full text-left rounded-md transition-colors duration-200',
                  {
                    'nav-item active': activeView === item.id
                  }
                )}
              >
                <div className="flex items-center space-x-3">
                  <span className="text-lg">{item.icon}</span>
                  <div>
                    <div className="font-medium">{item.name}</div>
                    <div className="text-xs text-gray-500">{item.description}</div>
                  </div>
                </div>
              </button>
            </li>
          ))}
        </ul>
      </nav>
      
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 text-center">
          <div>東京都感染症情報センター</div>
          <div className="mt-1">データ分析ダッシュボード</div>
        </div>
      </div>
    </aside>
  )
}