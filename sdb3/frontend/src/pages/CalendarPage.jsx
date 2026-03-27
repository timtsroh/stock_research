import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { Calendar, momentLocalizer } from 'react-big-calendar'
import moment from 'moment'
import 'react-big-calendar/lib/css/react-big-calendar.css'

const localizer = momentLocalizer(moment)

function ddayLabel(value) {
  if (value === 0) return { label: 'D-Day', className: 'text-amber-600' }
  if (value > 0) return { label: `D-${value}`, className: value <= 7 ? 'text-orange-600' : 'text-slate-600' }
  return { label: `D+${Math.abs(value)}`, className: 'text-slate-500' }
}

export default function CalendarPage() {
  const [events, setEvents] = useState([])
  const [filters, setFilters] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState('month')

  useEffect(() => {
    loadFilters()
    loadEvents()
  }, [])

  async function loadFilters() {
    try {
      const { data } = await axios.get('/api/calendar/filters')
      setFilters(data)
    } catch {
      setFilters([])
    }
  }

  async function loadEvents() {
    setLoading(true)
    try {
      const { data } = await axios.get('/api/calendar/events')
      setEvents(data)
      setSelected(current => data.find(item => item.title === current?.title && item.date === current?.date) || data[0] || null)
    } catch {
      setEvents([])
    } finally {
      setLoading(false)
    }
  }

  async function toggleFilter(key, enabled) {
    try {
      await axios.put(`/api/calendar/filters/${key}`, { enabled })
      setFilters(previous => previous.map(filter => (filter.key === key ? { ...filter, enabled } : filter)))
      await loadEvents()
    } catch {
      return null
    }
  }

  async function toggleAllFilters(enabled) {
    await Promise.all(filters.map(filter => axios.put(`/api/calendar/filters/${filter.key}`, { enabled })))
    setFilters(previous => previous.map(filter => ({ ...filter, enabled })))
    await loadEvents()
  }

  const calendarEvents = useMemo(() => {
    return events.map(event => ({
      title: event.title,
      start: new Date(`${event.date}T09:00:00`),
      end: new Date(`${event.date}T10:00:00`),
      allDay: true,
      resource: event,
    }))
  }, [events])

  const upcoming = useMemo(() => {
    return events
      .filter(event => event.d_day >= 0)
      .sort((left, right) => left.d_day - right.d_day)
      .slice(0, 10)
  }, [events])

  const activeFilterCount = filters.filter(filter => filter.enabled).length
  const allSelected = filters.length > 0 && filters.every(filter => filter.enabled)

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_340px]">
      <section className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-sky-700/80">Phase 3</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-900">이벤트 캘린더</h2>
            <p className="mt-2 text-sm text-slate-500">관심종목 실적과 주요 경제지표 일정을 월간 또는 주간 보기로 확인합니다.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {['month', 'week'].map(item => (
              <button
                key={item}
                onClick={() => setView(item)}
                className={`rounded-full px-4 py-2 text-sm transition ${
                  view === item ? 'bg-sky-600 text-white' : 'border border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                }`}
              >
                {item === 'month' ? '월간 보기' : '주간 보기'}
              </button>
            ))}
            <button
              onClick={loadEvents}
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50"
            >
              일정 새로고침
            </button>
          </div>
        </div>

        {loading ? (
          <div className="h-[680px] animate-pulse rounded-[28px] bg-slate-100" />
        ) : (
          <div className="rounded-[28px] border border-slate-200 bg-slate-50 p-4" style={{ height: 680 }}>
            <Calendar
              localizer={localizer}
              events={calendarEvents}
              startAccessor="start"
              endAccessor="end"
              style={{ height: '100%' }}
              eventPropGetter={event => ({
                style: {
                  backgroundColor: event.resource.color,
                  borderColor: event.resource.color,
                  color: '#fff',
                  borderRadius: '10px',
                  fontSize: '11px',
                },
              })}
              onSelectEvent={event => setSelected(event.resource)}
              views={['month', 'week']}
              view={view}
              onView={nextView => setView(nextView)}
            />
          </div>
        )}
      </section>

      <aside className="space-y-4">
        <section className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-slate-900">이벤트 필터</p>
            <span className="rounded-full bg-sky-50 px-3 py-1 text-xs text-sky-700">{activeFilterCount}개 활성화</span>
          </div>
          <label className="mt-4 flex cursor-pointer items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={event => toggleAllFilters(event.target.checked)}
              className="h-4 w-4 rounded border-slate-300"
            />
            <span className="text-sm font-medium text-slate-800">모두 선택/해제</span>
          </label>
          <div className="mt-3 space-y-3">
            {filters.map(filter => (
              <label key={filter.key} className="flex cursor-pointer items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3">
                <input
                  type="checkbox"
                  checked={filter.enabled}
                  onChange={event => toggleFilter(filter.key, event.target.checked)}
                  className="h-4 w-4 rounded border-slate-300"
                />
                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: filter.color }} />
                <span className="text-sm text-slate-700">{filter.label}</span>
              </label>
            ))}
          </div>
        </section>

        <section className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-semibold text-slate-900">다가오는 이벤트</p>
          <div className="mt-4 space-y-2">
            {upcoming.map(event => {
              const badge = ddayLabel(event.d_day)
              return (
                <button
                  key={`${event.key}-${event.date}-${event.title}`}
                  onClick={() => setSelected(event)}
                  className="flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 text-left transition hover:border-sky-300 hover:bg-sky-50"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm text-slate-900">{event.title}</p>
                    <p className="mt-1 text-xs text-slate-500">{event.date}</p>
                  </div>
                  <span className={`text-xs font-semibold ${badge.className}`}>{badge.label}</span>
                </button>
              )
            })}
            {upcoming.length === 0 ? <p className="text-sm text-slate-500">예정된 이벤트가 없습니다.</p> : null}
          </div>
        </section>

        <section className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-semibold text-slate-900">이벤트 상세</p>
          {selected ? (
            <div className="mt-4 space-y-3">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center gap-3">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: selected.color }} />
                  <p className="font-medium text-slate-900">{selected.title}</p>
                </div>
                <p className="mt-3 text-sm text-slate-600">{selected.detail || '상세 정보 없음'}</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Date</p>
                  <p className="mt-2 text-sm text-slate-900">{selected.date}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">D-Day</p>
                  <p className={`mt-2 text-sm font-semibold ${ddayLabel(selected.d_day).className}`}>{ddayLabel(selected.d_day).label}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Type</p>
                  <p className="mt-2 text-sm text-slate-900">{selected.type || selected.key}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Source</p>
                  <p className="mt-2 text-sm text-slate-900">{selected.source || '-'}</p>
                </div>
              </div>
              {selected.ticker ? (
                <div className="rounded-2xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700">
                  관심종목 연동: {selected.ticker}
                </div>
              ) : null}
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-500">캘린더에서 이벤트를 클릭하면 상세 정보가 표시됩니다.</p>
          )}
        </section>
      </aside>
    </div>
  )
}
