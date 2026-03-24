import { useState, useEffect, useMemo } from 'react'
import { Calendar, momentLocalizer } from 'react-big-calendar'
import moment from 'moment'
import 'react-big-calendar/lib/css/react-big-calendar.css'
import axios from 'axios'

const localizer = momentLocalizer(moment)

export default function CalendarPage() {
  const [events,  setEvents]  = useState([])
  const [filters, setFilters] = useState([])
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    axios.get('/api/calendar/events').then(r => setEvents(r.data))
    axios.get('/api/calendar/filters').then(r => setFilters(r.data))
  }, [])

  const reloadEvents = () =>
    axios.get('/api/calendar/events').then(r => setEvents(r.data))

  const toggleFilter = async (key, enabled) => {
    await axios.put(`/api/calendar/filters/${key}`, { enabled })
    setFilters(prev => prev.map(f => f.key === key ? { ...f, enabled } : f))
    reloadEvents()
  }

  const calEvents = useMemo(() => events.map(ev => ({
    title:    ev.title,
    start:    new Date(ev.date),
    end:      new Date(ev.date),
    allDay:   true,
    resource: ev,
  })), [events])

  const eventStyleGetter = (ev) => ({
    style: {
      backgroundColor: ev.resource?.color || '#3b82f6',
      border: 'none',
      fontSize: '11px',
      padding: '1px 4px',
    }
  })

  // 다가오는 이벤트 (오늘 이후 순)
  const upcoming = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10)
    return events.filter(e => e.date >= today)
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(0, 15)
  }, [events])

  return (
    <div className="flex flex-col xl:flex-row gap-6">
      {/* 캘린더 */}
      <div className="flex-1 bg-panel border border-border rounded-lg p-4" style={{ minHeight: 580 }}>
        <Calendar
          localizer={localizer}
          events={calEvents}
          startAccessor="start"
          endAccessor="end"
          style={{ height: 540 }}
          eventPropGetter={eventStyleGetter}
          onSelectEvent={ev => setSelected(ev.resource)}
          popup
        />
      </div>

      {/* 우측 패널 */}
      <div className="w-full xl:w-72 flex flex-col gap-4">
        {/* 이벤트 필터 */}
        <div className="bg-panel border border-border rounded-lg p-4">
          <h3 className="text-sm font-semibold mb-3 text-gray-200">이벤트 필터</h3>
          <div className="space-y-2">
            {filters.map(f => (
              <label key={f.key} className="flex items-center gap-2 cursor-pointer group">
                <input type="checkbox" checked={f.enabled}
                  onChange={e => toggleFilter(f.key, e.target.checked)}
                  className="rounded" />
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: f.color }} />
                <span className="text-sm text-gray-300 group-hover:text-gray-100">
                  {f.label}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* 다가오는 이벤트 */}
        <div className="bg-panel border border-border rounded-lg p-4 flex-1">
          <h3 className="text-sm font-semibold mb-3 text-gray-200">다가오는 이벤트</h3>
          <div className="space-y-1.5 overflow-y-auto max-h-72">
            {upcoming.map((ev, i) => {
              const today = new Date().toISOString().slice(0, 10)
              const dday  = Math.ceil((new Date(ev.date) - new Date(today)) / 86400000)
              return (
                <div key={i} onClick={() => setSelected(ev)}
                  className="flex items-center gap-2 py-1.5 px-2 rounded hover:bg-gray-800 cursor-pointer">
                  <span className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: ev.color }} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-200 truncate">{ev.title}</p>
                    <p className="text-xs text-gray-500">{ev.date}</p>
                  </div>
                  <span className={`text-xs font-mono flex-shrink-0
                    ${dday === 0 ? 'text-yellow-400' : dday <= 3 ? 'text-orange-400' : 'text-gray-500'}`}>
                    {dday === 0 ? 'D-Day' : `D-${dday}`}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* 선택된 이벤트 상세 */}
        {selected && (
          <div className="bg-panel border border-blue-600 rounded-lg p-4">
            <div className="flex justify-between items-start mb-1">
              <h4 className="text-sm font-semibold text-blue-300">{selected.title}</h4>
              <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-gray-300 text-xs">✕</button>
            </div>
            <p className="text-xs text-gray-400">{selected.date}</p>
            <span className="mt-2 inline-block text-xs px-2 py-0.5 rounded"
              style={{ backgroundColor: selected.color + '33', color: selected.color }}>
              {selected.key}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
