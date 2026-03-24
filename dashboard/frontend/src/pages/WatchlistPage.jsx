import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'

const API = '/api/watchlist'

function fmt(n, digits = 2) {
  if (n == null) return '—'
  return Number(n).toLocaleString('ko-KR', { maximumFractionDigits: digits })
}
function fmtCap(n) {
  if (n == null) return '—'
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`
  if (n >= 1e9)  return `$${(n / 1e9).toFixed(1)}B`
  if (n >= 1e8)  return `₩${(n / 1e8).toFixed(0)}억`
  return String(n)
}

export default function WatchlistPage() {
  const [stocks,   setStocks]   = useState([])
  const [selected, setSelected] = useState(null)
  const [fin,      setFin]      = useState(null)
  const [chart,    setChart]    = useState([])
  const [loading,  setLoading]  = useState(true)
  const [addTicker, setAddTicker] = useState('')
  const [addMarket, setAddMarket] = useState('US')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await axios.get(API)
      setStocks(data)
      if (data.length && !selected) setSelected(data[0].ticker)
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!selected) return
    axios.get(`${API}/${selected}/financials`).then(r => setFin(r.data))
    axios.get(`${API}/${selected}/chart`).then(r => setChart(r.data))
  }, [selected])

  const addStock = async () => {
    if (!addTicker.trim()) return
    try {
      await axios.post(API, { ticker: addTicker.toUpperCase(), market: addMarket })
      setAddTicker('')
      load()
    } catch { alert('추가 실패: 이미 있거나 잘못된 티커입니다.') }
  }

  const remove = async (ticker) => {
    await axios.delete(`${API}/${ticker}`)
    if (selected === ticker) setSelected(null)
    load()
  }

  const selStock = stocks.find(s => s.ticker === selected)

  return (
    <div>
      {/* 종목 추가 */}
      <div className="flex items-center gap-2 mb-4">
        <input value={addTicker} onChange={e => setAddTicker(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && addStock()}
          placeholder="티커 입력 (예: AAPL, 005930)"
          className="bg-panel border border-border rounded px-3 py-1.5 text-sm text-gray-100 w-56 focus:outline-none focus:border-blue-500" />
        <select value={addMarket} onChange={e => setAddMarket(e.target.value)}
          className="bg-panel border border-border rounded px-2 py-1.5 text-sm text-gray-300">
          <option value="US">미국</option>
          <option value="KR">한국</option>
        </select>
        <button onClick={addStock}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-1.5 rounded">
          + 추가
        </button>
        <button onClick={load}
          className="text-gray-400 hover:text-gray-100 text-sm px-3 py-1.5 border border-border rounded">
          ↻ 새로고침
        </button>
      </div>

      {loading && <div className="text-gray-400 text-sm py-8 text-center">데이터 로딩 중...</div>}

      {!loading && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* 종목 테이블 */}
          <div className="xl:col-span-2">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-gray-400 text-xs">
                  {['종목','시장','현재가','등락률','시총','PER','PBR','52주 고/저',''].map(h => (
                    <th key={h} className="py-2 px-2 text-left font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {stocks.map(s => (
                  <tr key={s.ticker}
                    onClick={() => setSelected(s.ticker)}
                    className={`border-b border-border cursor-pointer hover:bg-panel transition-colors
                      ${selected === s.ticker ? 'bg-blue-900/20' : ''}`}>
                    <td className="py-2.5 px-2 font-semibold text-blue-400">{s.ticker}</td>
                    <td className="py-2.5 px-2">
                      <span className={`text-xs px-1.5 py-0.5 rounded
                        ${s.market === 'KR' ? 'bg-red-900/40 text-red-300' : 'bg-blue-900/40 text-blue-300'}`}>
                        {s.market}
                      </span>
                    </td>
                    <td className="py-2.5 px-2 font-mono">{fmt(s.price)}</td>
                    <td className={`py-2.5 px-2 font-mono font-semibold
                      ${(s.change_pct ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {s.change_pct != null ? `${s.change_pct >= 0 ? '+' : ''}${s.change_pct}%` : '—'}
                    </td>
                    <td className="py-2.5 px-2 text-gray-300">{fmtCap(s.market_cap)}</td>
                    <td className="py-2.5 px-2 text-gray-300">{s.per != null ? `${fmt(s.per)}x` : '—'}</td>
                    <td className="py-2.5 px-2 text-gray-300">{s.pbr != null ? `${fmt(s.pbr)}x` : '—'}</td>
                    <td className="py-2.5 px-2 text-gray-400 text-xs">
                      {s.week52_high != null ? `${fmt(s.week52_high)} / ${fmt(s.week52_low)}` : '—'}
                    </td>
                    <td className="py-2.5 px-2">
                      <button onClick={e => { e.stopPropagation(); remove(s.ticker) }}
                        className="text-gray-600 hover:text-red-400 text-xs">✕</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 상세 패널 */}
          {selStock && (
            <div className="bg-panel border border-border rounded-lg p-4">
              <h2 className="font-bold text-base mb-1">{selStock.name || selStock.ticker}</h2>
              <p className="text-gray-400 text-xs mb-4">{selStock.ticker} · {selStock.market}</p>

              {/* 주가 차트 */}
              <p className="text-xs text-gray-400 mb-1">주가 (1년)</p>
              <ResponsiveContainer width="100%" height={120}>
                <LineChart data={chart}>
                  <Line type="monotone" dataKey="close" stroke="#3b82f6" dot={false} strokeWidth={1.5} />
                  <XAxis dataKey="date" hide />
                  <YAxis domain={['auto','auto']} hide />
                  <Tooltip contentStyle={{ background:'#161b22', border:'1px solid #30363d', fontSize:11 }}
                    formatter={v => [fmt(v), '가격']} labelFormatter={l => l} />
                </LineChart>
              </ResponsiveContainer>

              {/* 재무 차트 */}
              {fin && fin.quarters.length > 0 && (
                <>
                  <p className="text-xs text-gray-400 mt-4 mb-1">분기 실적 (십억)</p>
                  <ResponsiveContainer width="100%" height={150}>
                    <BarChart data={fin.quarters.map((q, i) => ({
                      q: q.slice(0, 7),
                      매출: fin.revenue[i],
                      영업이익: fin.operating_income[i],
                      순이익: fin.net_income[i],
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                      <XAxis dataKey="q" tick={{ fontSize: 9, fill: '#9ca3af' }} />
                      <YAxis tick={{ fontSize: 9, fill: '#9ca3af' }} />
                      <Tooltip contentStyle={{ background:'#161b22', border:'1px solid #30363d', fontSize:11 }} />
                      <Bar dataKey="매출"    fill="#3b82f6" radius={[2,2,0,0]} />
                      <Bar dataKey="영업이익" fill="#22c55e" radius={[2,2,0,0]} />
                      <Bar dataKey="순이익"  fill="#a855f7" radius={[2,2,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
