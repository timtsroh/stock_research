import { useState } from 'react'
import WatchlistPage from './pages/WatchlistPage'
import MacroPage from './pages/MacroPage'
import CalendarPage from './pages/CalendarPage'

const TABS = [
  { id: 'watchlist', label: '관심종목', desc: '주가와 재무를 빠르게 점검합니다.' },
  { id: 'macro', label: '거시변수', desc: '6개 시장 지표를 기간별로 비교합니다.' },
  { id: 'calendar', label: '캘린더', desc: '실적과 경제 이벤트 일정을 관리합니다.' },
]

export default function App() {
  const [tab, setTab] = useState('watchlist')

  return (
    <div className="min-h-screen bg-app text-slate-900">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.16),_transparent_32%),radial-gradient(circle_at_top_right,_rgba(251,191,36,0.14),_transparent_26%)] pointer-events-none" />
      <div className="relative">
        <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/80 backdrop-blur">
          <div className="mx-auto flex max-w-[1440px] flex-col gap-4 px-4 py-4 lg:px-6">
            <div className="flex justify-end">
              <div className="grid grid-cols-3 gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-1">
                {TABS.map(item => (
                  <button
                    key={item.id}
                    onClick={() => setTab(item.id)}
                    className={`rounded-2xl px-4 py-3 text-sm transition ${
                      tab === item.id
                        ? 'bg-sky-600 text-white shadow-[0_10px_30px_rgba(14,165,233,0.24)]'
                        : 'text-slate-600 hover:bg-white hover:text-slate-900'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-[1440px] px-4 py-6 lg:px-6 lg:py-8">
          {tab === 'watchlist' && <WatchlistPage />}
          {tab === 'macro' && <MacroPage />}
          {tab === 'calendar' && <CalendarPage />}
        </main>
      </div>
    </div>
  )
}
