import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid, Legend
} from 'recharts'

const SORT_OPTIONS = [
  { value: 'market_cap', label: '시가총액' },
  { value: 'change_pct', label: '등락률' },
  { value: 'per',        label: 'PER' },
]

function fmtCap(v) {
  if (!v) return '-'
  if (v >= 1e12) return (v / 1e12).toFixed(1) + 'T'
  if (v >= 1e9)  return (v / 1e9).toFixed(1)  + 'B'
  if (v >= 1e6)  return (v / 1e6).toFixed(1)  + 'M'
  return v
}

function fmtNum(v, digits = 2) {
  if (v == null) return '-'
  return Number(v).toFixed(digits)
}

export default function WatchlistPage() {
  const [stocks,      setStocks]      = useState([])
  const [loading,     setLoading]     = useState(true)
  const [selected,    setSelected]    = useState(null)
  const [chartData,   setChartData]   = useState([])
  const [finData,     setFinData]     = useState(null)
  const [chartPeriod, setChartPeriod] = useState('1y')
  const [sortBy,      setSortBy]      = useState('market_cap')
  const [ticker,      setTicker]      = useState('')
  const [market,      setMarket]      = useState('US')
  const [adding,      setAdding]      = useState(false)
  const [err,         setErr]         = useState('')

  useEffect(() => { loadWatchlist() }, [])

  useEffect(() => {
    if (selected) {
      loadChart(selected.ticker, chartPeriod)
      loadFinancials(selected.ticker)
    }
  }, [selected, chartPeriod])

  async function loadWatchlist() {
    setLoading(true)
    try {
      const { data } = await axios.get('/api/watchlist/')
      setStocks(data)
    } catch {
      setErr('데이터 로딩 실패')
    } finally {
      setLoading(false)
    }
  }

  async function loadChart(t, period) {
    try {
      const { data } = await axios.get(`/api/watchlist/${t}/chart?period=${period}`)
      setChartData(data)
    } catch {
      setChartData([])
    }
  }

  async function loadFinancials(t) {
    try {
      const { data } = await axios.get(`/api/watchlist/${t}/financials`)
      setFinData(data)
    } catch {
      setFinData(null)
    }
  }

  async function addStock() {
    if (!ticker.trim()) return
    setAdding(true)
    setErr('')
    try {
      await axios.post('/api/watchlist/', { ticker: ticker.trim().toUpperCase(), market })
      setTicker('')
      await loadWatchlist()
    } catch (e) {
      setErr(e.response?.data?.detail || '추가 실패')
    } finally {
      setAdding(false)
    }
  }

  async function removeStock(t, e) {
    e.stopPropagation()
    try {
      await axios.delete(`/api/watchlist/${t}`)
      if (selected?.ticker === t) setSelected(null)
      await loadWatchlist()
    } catch {
      setErr('삭제 실패')
    }
  }

  const sorted = [...stocks].sort((a, b) => {
    const av = a[sortBy] ?? -Infinity
    const bv = b[sortBy] ?? -Infinity
    return bv - av
  })

  const finChartData = finData
    ? finData.quarters.map((q, i) => ({
        q,
        매출액: finData.revenue?.[i],
        영업이익: finData.operating_income?.[i],
        순이익: finData.net_income?.[i],
      })).reverse()
    : []

  return (
    <div>
      {/* 헤더: 추가 폼 + 정렬 */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <input
          value={ticker}
          onChange={e => setTicker(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && addStock()}
          placeholder="티커 입력 (예: AAPL)"
          className="bg-panel border border-border rounded px-3 py-1.5 text-sm w-40 focus:outline-none focus:border-blue-500"
        />
        <select
          value={market}
          onChange={e => setMarket(e.target.value)}
          className="bg-panel border border-border rounded px-2 py-1.5 text-sm focus:outline-none"
        >
          <option value="US">US</option>
          <option value="KR">KR</option>
        </select>
        <button
          onClick={addStock}
          disabled={adding}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1.5 rounded disabled:opacity-50"
        >
          {adding ? '추가 중...' : '+ 추가'}
        </button>
        <div className="ml-auto flex items-center gap-2 text-sm">
          <span className="text-gray-400">정렬:</span>
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="bg-panel border border-border rounded px-2 py-1.5 text-sm focus:outline-none"
          >
            {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      </div>
      {err && <p className="text-red-400 text-sm mb-3">{err}</p>}

      <div className="flex gap-4">
        {/* 테이블 */}
        <div className="flex-1 min-w-0">
          {loading ? (
            <div className="space-y-2">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-10 bg-panel rounded animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 border-b border-border text-left">
                    <th className="py-2 pr-4">종목</th>
                    <th className="py-2 pr-4">현재가</th>
                    <th className="py-2 pr-4">등락률</th>
                    <th className="py-2 pr-4">시총</th>
                    <th className="py-2 pr-4">PER</th>
                    <th className="py-2 pr-4">PBR</th>
                    <th className="py-2 pr-4">52W 고</th>
                    <th className="py-2 pr-4">52W 저</th>
                    <th className="py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map(s => (
                    <tr
                      key={s.ticker}
                      onClick={() => setSelected(s)}
                      className={`border-b border-border cursor-pointer hover:bg-panel transition-colors ${
                        selected?.ticker === s.ticker ? 'bg-panel' : ''
                      }`}
                    >
                      <td className="py-2 pr-4">
                        <div className="font-mono font-semibold">{s.ticker}</div>
                        <div className="text-gray-400 text-xs truncate max-w-[100px]">{s.name}</div>
                      </td>
                      <td className="py-2 pr-4 font-mono">
                        {s.price != null ? fmtNum(s.price) : '-'}
                      </td>
                      <td className={`py-2 pr-4 font-mono ${
                        s.change_pct > 0 ? 'text-green-400' : s.change_pct < 0 ? 'text-red-400' : 'text-gray-300'
                      }`}>
                        {s.change_pct != null ? (s.change_pct > 0 ? '+' : '') + fmtNum(s.change_pct) + '%' : '-'}
                      </td>
                      <td className="py-2 pr-4 text-gray-300">{fmtCap(s.market_cap)}</td>
                      <td className="py-2 pr-4 text-gray-300">{s.per ? fmtNum(s.per) + 'x' : '-'}</td>
                      <td className="py-2 pr-4 text-gray-300">{s.pbr ? fmtNum(s.pbr) + 'x' : '-'}</td>
                      <td className="py-2 pr-4 text-gray-300">{s.week52_high ? fmtNum(s.week52_high) : '-'}</td>
                      <td className="py-2 pr-4 text-gray-300">{s.week52_low  ? fmtNum(s.week52_low)  : '-'}</td>
                      <td className="py-2">
                        <button
                          onClick={e => removeStock(s.ticker, e)}
                          className="text-gray-500 hover:text-red-400 text-xs px-1"
                        >✕</button>
                      </td>
                    </tr>
                  ))}
                  {sorted.length === 0 && (
                    <tr><td colSpan={9} className="py-8 text-center text-gray-500">종목을 추가하세요</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 디테일 패널 */}
        {selected && (
          <div className="w-[380px] shrink-0 bg-panel border border-border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <span className="font-mono font-bold text-base">{selected.ticker}</span>
                <span className="text-gray-400 text-xs ml-2">{selected.name}</span>
              </div>
              <div className="flex gap-1">
                {['1y','3y','5y'].map(p => (
                  <button key={p} onClick={() => setChartPeriod(p)}
                    className={`px-2 py-0.5 text-xs rounded ${
                      chartPeriod === p ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    }`}>
                    {p.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            {/* 주가 차트 */}
            <div className="mb-4">
              <p className="text-xs text-gray-400 mb-1">주가 추이</p>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={140}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                    <XAxis dataKey="date" hide />
                    <YAxis domain={['auto','auto']} width={50} tick={{ fontSize: 10, fill: '#9ca3af' }} />
                    <Tooltip
                      contentStyle={{ background: '#161b22', border: '1px solid #30363d', fontSize: 11 }}
                      formatter={v => [fmtNum(v), '종가']}
                    />
                    <Line type="monotone" dataKey="close" stroke="#3b82f6" dot={false} strokeWidth={1.5} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[140px] flex items-center justify-center text-gray-500 text-xs">데이터 없음</div>
              )}
            </div>

            {/* 재무제표 */}
            <div>
              <p className="text-xs text-gray-400 mb-1">분기 실적 (십억)</p>
              {finChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={finChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                    <XAxis dataKey="q" tick={{ fontSize: 9, fill: '#9ca3af' }} />
                    <YAxis width={40} tick={{ fontSize: 10, fill: '#9ca3af' }} />
                    <Tooltip
                      contentStyle={{ background: '#161b22', border: '1px solid #30363d', fontSize: 11 }}
                    />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                    <Bar dataKey="매출액"   fill="#3b82f6" />
                    <Bar dataKey="영업이익" fill="#22c55e" />
                    <Bar dataKey="순이익"   fill="#a855f7" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[160px] flex items-center justify-center text-gray-500 text-xs">데이터 없음</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
