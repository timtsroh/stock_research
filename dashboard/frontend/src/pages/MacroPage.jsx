import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  LineChart, Line, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'

const PERIODS = ['1y', '3y', '5y']
const COLORS  = ['#3b82f6','#22c55e','#f97316','#a855f7','#ef4444','#38bdf8']

function MacroChart({ panel, period }) {
  const [data,    setData]    = useState({ data: [], latest: null, change: null })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!panel) return
    setLoading(true)
    axios.get(`/api/macro/chart/${encodeURIComponent(panel.ticker)}?period=${period}`)
      .then(r => setData(r.data))
      .finally(() => setLoading(false))
  }, [panel, period])

  const isPos = (data.change ?? 0) >= 0

  return (
    <div className="bg-panel border border-border rounded-lg p-4 flex flex-col">
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="text-xs text-gray-400">{panel?.label}</p>
          {data.latest != null && (
            <p className="text-xl font-bold font-mono mt-0.5">
              {Number(data.latest).toLocaleString('en-US', { maximumFractionDigits: 4 })}
            </p>
          )}
        </div>
        {data.change != null && (
          <span className={`text-xs font-semibold px-2 py-0.5 rounded
            ${isPos ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}`}>
            {isPos ? '+' : ''}{data.change}%
          </span>
        )}
      </div>

      {loading
        ? <div className="flex-1 flex items-center justify-center text-gray-600 text-xs">로딩 중...</div>
        : (
          <ResponsiveContainer width="100%" height={130}>
            <LineChart data={data.data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
              <Line type="monotone" dataKey="close"
                stroke={COLORS[panel?.slot ?? 0]}
                dot={false} strokeWidth={1.5} />
              <XAxis dataKey="date" tick={{ fontSize: 8, fill: '#6b7280' }}
                tickFormatter={v => v.slice(2, 7)} interval="preserveStartEnd" />
              <YAxis domain={['auto','auto']} tick={{ fontSize: 8, fill: '#6b7280' }}
                width={45} tickFormatter={v => v.toLocaleString()} />
              <Tooltip
                contentStyle={{ background:'#161b22', border:'1px solid #30363d', fontSize:11 }}
                formatter={v => [Number(v).toLocaleString('en-US', { maximumFractionDigits: 4 }), panel?.label]}
                labelFormatter={l => l} />
            </LineChart>
          </ResponsiveContainer>
        )
      }
    </div>
  )
}

export default function MacroPage() {
  const [panels,  setPanels]  = useState([])
  const [period,  setPeriod]  = useState('5y')
  const [presets, setPresets] = useState([])
  const [editing, setEditing] = useState(null)

  useEffect(() => {
    axios.get('/api/macro/panels').then(r => setPanels(r.data))
    axios.get('/api/macro/presets').then(r => setPresets(r.data))
  }, [])

  const savePanel = async (slot, ticker, label) => {
    await axios.put(`/api/macro/panels/${slot}`, { ticker, label })
    const { data } = await axios.get('/api/macro/panels')
    setPanels(data)
    setEditing(null)
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-6">
        <span className="text-sm text-gray-400 mr-2">기간</span>
        {PERIODS.map(p => (
          <button key={p} onClick={() => setPeriod(p)}
            className={`text-xs px-3 py-1 rounded border transition-colors
              ${period === p
                ? 'bg-blue-600 border-blue-600 text-white'
                : 'border-border text-gray-400 hover:border-gray-500'}`}>
            {p.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {panels.map(panel => (
          <div key={panel.slot} className="relative group">
            <MacroChart panel={{ ...panel, slot: panel.slot }} period={period} />
            <button onClick={() => setEditing(panel.slot)}
              className="absolute top-2 right-2 text-gray-600 hover:text-gray-300 text-xs
                opacity-0 group-hover:opacity-100 transition-opacity">
              ✏
            </button>

            {editing === panel.slot && (
              <div className="absolute inset-0 bg-panel border border-blue-500 rounded-lg p-4 z-10">
                <p className="text-xs text-gray-400 mb-2">패널 {panel.slot + 1} 지표 변경</p>
                <select onChange={e => {
                    const p = presets.find(x => x.ticker === e.target.value)
                    if (p) savePanel(panel.slot, p.ticker, p.label)
                  }}
                  className="w-full bg-surface border border-border rounded px-2 py-1.5 text-sm text-gray-100 mb-2">
                  <option value="">지표 선택...</option>
                  {presets.map(p => (
                    <option key={p.ticker} value={p.ticker}>{p.label}</option>
                  ))}
                </select>
                <button onClick={() => setEditing(null)}
                  className="text-xs text-gray-500 hover:text-gray-300">취소</button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
