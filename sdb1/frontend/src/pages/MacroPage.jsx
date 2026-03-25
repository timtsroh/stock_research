import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  LineChart, Line, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'

const PANEL_COLORS = ['#3b82f6','#22c55e','#f97316','#ef4444','#a855f7','#eab308']

function MacroPanel({ panel, color, period, onUpdate, presets }) {
  const [data,     setData]     = useState({ data: [], latest: null, change: null })
  const [loading,  setLoading]  = useState(true)
  const [editing,  setEditing]  = useState(false)
  const [selTicker, setSelTicker] = useState(panel.ticker)

  useEffect(() => {
    loadData(panel.ticker, period)
  }, [panel.ticker, period])

  async function loadData(ticker, p) {
    setLoading(true)
    try {
      const { data: d } = await axios.get(`/api/macro/chart/${encodeURIComponent(ticker)}?period=${p}`)
      setData(d)
    } catch {
      setData({ data: [], latest: null, change: null })
    } finally {
      setLoading(false)
    }
  }

  async function savePanel() {
    const preset = presets.find(p => p.ticker === selTicker)
    if (!preset) return
    await axios.put(`/api/macro/panels/${panel.slot}`, { ticker: preset.ticker, label: preset.label })
    onUpdate()
    setEditing(false)
  }

  const changeColor = data.change > 0 ? 'text-green-400' : data.change < 0 ? 'text-red-400' : 'text-gray-300'

  return (
    <div className="bg-panel border border-border rounded-lg p-4 relative group">
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="text-xs text-gray-400">{panel.label}</p>
          {loading ? (
            <div className="h-6 w-24 bg-gray-700 rounded animate-pulse mt-1" />
          ) : (
            <p className="text-lg font-mono font-bold">
              {data.latest != null ? data.latest.toLocaleString() : '-'}
              {data.change != null && (
                <span className={`text-xs ml-2 ${changeColor}`}>
                  {data.change > 0 ? '+' : ''}{data.change}%
                </span>
              )}
            </p>
          )}
        </div>
        <button
          onClick={() => setEditing(v => !v)}
          className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-gray-200 text-xs transition-opacity"
        >편집</button>
      </div>

      {editing && (
        <div className="mb-2 flex gap-1">
          <select
            value={selTicker}
            onChange={e => setSelTicker(e.target.value)}
            className="flex-1 bg-surface border border-border rounded px-2 py-1 text-xs focus:outline-none"
          >
            {presets.map(p => (
              <option key={p.ticker} value={p.ticker}>{p.label} ({p.ticker})</option>
            ))}
          </select>
          <button onClick={savePanel}
            className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-2 py-1 rounded">
            저장
          </button>
          <button onClick={() => setEditing(false)}
            className="text-gray-400 hover:text-gray-200 text-xs px-2 py-1">
            취소
          </button>
        </div>
      )}

      {loading ? (
        <div className="h-[120px] flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : data.data.length > 0 ? (
        <ResponsiveContainer width="100%" height={120}>
          <LineChart data={data.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
            <XAxis dataKey="date" hide />
            <YAxis domain={['auto','auto']} hide />
            <Tooltip
              contentStyle={{ background: '#161b22', border: '1px solid #30363d', fontSize: 11 }}
              formatter={v => [v, panel.label]}
              labelFormatter={l => l}
            />
            <Line type="monotone" dataKey="close" stroke={color} dot={false} strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-[120px] flex items-center justify-center text-gray-500 text-xs">데이터 없음</div>
      )}
    </div>
  )
}

export default function MacroPage() {
  const [panels,  setPanels]  = useState([])
  const [presets, setPresets] = useState([])
  const [period,  setPeriod]  = useState('5y')

  useEffect(() => {
    loadPanels()
    loadPresets()
  }, [])

  async function loadPanels() {
    try {
      const { data } = await axios.get('/api/macro/panels')
      setPanels(data)
    } catch {}
  }

  async function loadPresets() {
    try {
      const { data } = await axios.get('/api/macro/presets')
      setPresets(data)
    } catch {}
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-300">거시경제 지표</h2>
        <div className="flex gap-1">
          {['1y','3y','5y'].map(p => (
            <button key={p} onClick={() => setPeriod(p)}
              className={`px-3 py-1 text-xs rounded ${
                period === p ? 'bg-blue-600 text-white' : 'bg-panel text-gray-400 hover:bg-gray-700 border border-border'
              }`}>
              {p.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {panels.map((panel, i) => (
          <MacroPanel
            key={panel.slot}
            panel={panel}
            color={PANEL_COLORS[i % PANEL_COLORS.length]}
            period={period}
            presets={presets}
            onUpdate={loadPanels}
          />
        ))}
        {panels.length === 0 && [...Array(6)].map((_, i) => (
          <div key={i} className="bg-panel border border-border rounded-lg h-[200px] animate-pulse" />
        ))}
      </div>
    </div>
  )
}
