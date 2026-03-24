import { useState } from 'react'
import WatchlistPage  from './pages/WatchlistPage'
import MacroPage      from './pages/MacroPage'
import CalendarPage   from './pages/CalendarPage'

const TABS = [
  { id: 'watchlist', label: '관심종목' },
  { id: 'macro',     label: '거시변수' },
  { id: 'calendar',  label: '캘린더'   },
]

export default function App() {
  const [tab, setTab] = useState('watchlist')

  return (
    <div className="min-h-screen bg-surface">
      {/* 상단 네비게이션 */}
      <header className="bg-panel border-b border-border sticky top-0 z-50">
        <div className="max-w-screen-xl mx-auto px-4 flex items-center gap-1 h-12">
          <span className="text-blue-400 font-bold text-sm mr-6">◆ Stock Research</span>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-4 py-2 text-sm rounded transition-colors
                ${tab === t.id
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'}`}>
              {t.label}
            </button>
          ))}
        </div>
      </header>

      {/* 본문 */}
      <main className="max-w-screen-xl mx-auto px-4 py-6">
        {tab === 'watchlist' && <WatchlistPage />}
        {tab === 'macro'     && <MacroPage />}
        {tab === 'calendar'  && <CalendarPage />}
      </main>
    </div>
  )
}
