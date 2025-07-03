import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '東京都感染症ダッシュボード',
  description: '東京都の感染症発生動向を可視化するダッシュボード',
  keywords: ['感染症', '東京都', 'ダッシュボード', 'データ可視化'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className={inter.className}>
        <div className="dashboard-container">
          {children}
        </div>
      </body>
    </html>
  )
}