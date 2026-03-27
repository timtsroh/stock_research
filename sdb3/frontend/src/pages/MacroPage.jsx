import { useEffect, useState } from 'react'
import axios from 'axios'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const PANEL_COLORS = ['#0284c7', '#059669', '#ea580c', '#dc2626', '#7c3aed', '#db2777']

function MacroPanel({ panel, color, period, onUpdate, presets }) {
  const [data, setData] = useState({ data: [], latest: null, change: null })
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [selectedTicker, setSelectedTicker] = useState(panel.ticker)

  useEffect(() => {
    setSelectedTicker(panel.ticker)
  }, [panel.ticker])

  useEffect(() => {
    loadData(panel.ticker, period)
  }, [panel.ticker, period])

  async function loadData(ticker, currentPeriod) {
    setLoading(true)
    try {
      const { data: response } = await axios.get(`/api/macro/chart/${encodeURIComponent(ticker)}?period=${currentPeriod}`)
      setData(response)
    } catch {
      setData({ data: [], latest: null, change: null })
    } finally {
      setLoading(false)
    }
  }

  async function savePanel() {
    const preset = presets.find(item => item.ticker === selectedTicker)
    if (!preset) return
    await axios.put(`/api/macro/panels/${panel.slot}`, { ticker: preset.ticker, label: preset.label })
    onUpdate()
    setEditing(false)
  }

  return (
    <article className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Macro Panel</p>
          <h3 className="mt-2 text-lg font-semibold text-slate-900">{panel.label}</h3>
          <div className="mt-2 flex items-center gap-3">
            <span className="text-2xl font-semibold text-slate-900">
              {data.latest != null ? Number(data.latest).toLocaleString() : '-'}
            </span>
            {data.change != null ? (
              <span className={`rounded-full px-2 py-1 text-xs ${data.change >= 0 ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
                {data.change > 0 ? '+' : ''}
                {data.change}%
              </span>
            ) : null}
          </div>
        </div>
        <button
          onClick={() => setEditing(value => !value)}
          className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600 transition hover:bg-slate-100"
        >
          {editing ? '닫기' : '패널 편집'}
        </button>
      </div>

      {editing ? (
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <select
            value={selectedTicker}
            onChange={event => setSelectedTicker(event.target.value)}
            className="flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none focus:border-sky-500"
          >
            {presets.map(preset => (
              <option key={preset.ticker} value={preset.ticker}>
                {preset.label} ({preset.ticker})
              </option>
            ))}
          </select>
          <button
            onClick={savePanel}
            className="rounded-2xl bg-sky-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-sky-700"
          >
            저장
          </button>
        </div>
      ) : null}

      <div className="mt-4">
        {loading ? (
          <div className="h-[180px] animate-pulse rounded-3xl bg-slate-100" />
        ) : data.data.length > 0 ? (
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={data.data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#dbe4f0" />
              <XAxis dataKey="date" hide />
              <YAxis hide />
              <Tooltip
                contentStyle={{ background: '#ffffff', border: '1px solid #dbe4f0', borderRadius: 16 }}
                formatter={value => [Number(value).toLocaleString(), panel.label]}
              />
              <Line type="monotone" dataKey="close" stroke={color} dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-[180px] items-center justify-center rounded-3xl bg-slate-50 text-sm text-slate-500">
            데이터를 가져오지 못했습니다.
          </div>
        )}
      </div>
    </article>
  )
}

export default function MacroPage() {
  const [panels, setPanels] = useState([])
  const [presets, setPresets] = useState([])
  const [period, setPeriod] = useState('5y')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadPage()
  }, [])

  async function loadPage() {
    setLoading(true)
    try {
      const [panelResponse, presetResponse] = await Promise.all([
        axios.get('/api/macro/panels'),
        axios.get('/api/macro/presets'),
      ])
      setPanels(panelResponse.data)
      setPresets(presetResponse.data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-sky-700/80">Phase 1</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-900">거시경제 6패널 모니터</h2>
            <p className="mt-2 text-sm text-slate-500">미국 금리, 지수, 달러, 유가, 변동성, 나스닥 100을 1Y / 3Y / 5Y로 비교합니다.</p>
          </div>

          <div className="flex flex-wrap gap-2">
            {['1y', '3y', '5y'].map(item => (
              <button
                key={item}
                onClick={() => setPeriod(item)}
                className={`rounded-full px-4 py-2 text-sm transition ${
                  period === item ? 'bg-sky-600 text-white' : 'border border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                }`}
              >
                {item.toUpperCase()}
              </button>
            ))}
            <button
              onClick={loadPage}
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50"
            >
              패널 새로고침
            </button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {loading
          ? Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="h-[280px] animate-pulse rounded-[28px] bg-slate-100" />
            ))
          : panels.map((panel, index) => (
              <MacroPanel
                key={panel.slot}
                panel={panel}
                color={PANEL_COLORS[index % PANEL_COLORS.length]}
                period={period}
                presets={presets}
                onUpdate={loadPage}
              />
            ))}
      </section>
    </div>
  )
}
