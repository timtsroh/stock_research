import { useState, useEffect, useMemo } from 'react'
import axios from 'axios'
import { Calendar, momentLocalizer } from 'react-big-calendar'
import moment from 'moment'
import 'react-big-calendar/lib/css/react-big-calendar.css'

const localizer = momentLocalizer(moment)

function dday(dateStr) {
  const today = new Date()
  today.setHours(0,0,0,0)
  const target = new Date(dateStr)
  target.setHours(0,0,0,0)
  const diff = Math.round((target - today) / 86400000)
  if (diff === 0) return { label: 'D-Day', cls: 'text-yellow-400' }
  if (diff > 0)   return { label: `D-${diff}`, cls: diff <= 7 ? 'text-orange-400' : 'text-gray-400' }
  return { label: `D+${Math.abs(diff)}`, cls: 'text-gray-600' }
}

export default function CalendarPage() {
  const [events,    setEvents]    = useState([])
  const [filters,   setFilters]   = useState([])
  const [selected,  setSelected]  = useState(null)
  const [loading,   setLoading]   = useState(true)

  useEffect(() => {
    loadFilters()
    loadEvents()
  }, [])

  async function loadFilters() {
    try {
      const { data } = await axios.get('/api/calendar/filters')
      setFilters(data)
    } catch {}
  }

  async function loadEvents() {
    setLoading(true)
    try {
      const { data } = await axios.get('/api/calendar/events')
      setEvents(data)
    } catch {
      setEvents([])
    } finally {
      setLoading(false)
    }
  }

  async function toggleFilter(key, enabled) {
    try {
      await axios.put(`/api/calendar/filters/${key}`, { enabled })
      setFilters(prev => prev.map(f => f.key === key ? { ...f, enabled } : f))
      await loadEvents()
    } catch {}
  }

  const calEvents = useMemo(() =>
    events.map(ev => ({
      title: ev.title,
      start: new Date(ev.date),
      end:   new Date(ev.date),
      allDay: true,
      resource: ev,
    })), [events])

  const upcoming = useMemo(() => {
    const today = new Date()
    today.setHours(0,0,0,0)
    return events
      .filter(ev => new Date(ev.date) >= today)
      .slice(0, 10)
  }, [events])

  const eventStyleGetter = (event) => ({
    style: {
      backgroundColor: event.resource.color,
      borderColor: event.resource.color,
      color: '#fff',
      fontSize: '11px',
    }
  })

  return (
    <div className="flex gap-4">
      {/* 캘린더 */}
      <div className="flex-1 min-w-0">
        {loading ? (
          <div className="h-[600px] bg-panel rounded-lg animate-pulse" />
        ) : (
          <div className="bg-panel border border-border rounded-lg p-4" style={{ height: 620 }}>
            <Calendar
              localizer={localizer}
              events={calEvents}
              startAccessor="start"
              endAccessor="end"
              style={{ height: '100%' }}
              eventPropGetter={eventStyleGetter}
              onSelectEvent={ev => setSelected(ev.resource)}
              views={['month']}
              defaultView="month"
            />
          </div>
        )}

        {/* 이벤트 상세 카드 */}
        {selected && (
          <div className="mt-3 bg-panel border border-border rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: selected.color }} />
              <div>
                <p className="font-semibold text-sm">{selected.title}</p>
                <p className="text-xs text-gray-400">{selected.date}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-sm font-mono font-bold ${dday(selected.date).cls}`}>
                {dday(selected.date).label}
              </span>
              <button onClick={() => setSelected(null)}
                className="text-gray-500 hover:text-gray-200 text-xs">✕</button>
            </div>
          </div>
        )}
      </div>

      {/* 사이드바 */}
      <div className="w-56 shrink-0 space-y-4">
        {/* 필터 */}
        <div className="bg-panel border border-border rounded-lg p-4">
          <p className="text-xs font-semibold text-gray-300 mb-3">이벤트 필터</p>
          <div className="space-y-2">
            {filters.map(f => (
              <label key={f.key} className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={f.enabled}
                  onChange={e => toggleFilter(f.key, e.target.checked)}
                  className="rounded"
                />
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: f.color }} />
                <span className="text-xs text-gray-300 group-hover:text-white">{f.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* 다가오는 이벤트 */}
        <div className="bg-panel border border-border rounded-lg p-4">
          <p className="text-xs font-semibold text-gray-300 mb-3">다가오는 이벤트</p>
          <div className="space-y-2">
            {upcoming.map((ev, i) => {
              const dd = dday(ev.date)
              return (
                <div key={i}
                  onClick={() => setSelected(ev)}
                  className="flex items-center justify-between cursor-pointer hover:bg-surface rounded px-1 py-0.5"
                >
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: ev.color }} />
                    <span className="text-xs text-gray-300 truncate">{ev.title}</span>
                  </div>
                  <span className={`text-xs font-mono shrink-0 ml-1 ${dd.cls}`}>{dd.label}</span>
                </div>
              )
            })}
            {upcoming.length === 0 && (
              <p className="text-xs text-gray-500">예정된 이벤트 없음</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
