const SHANGHAI_OFFSET_MS = 8 * 60 * 60 * 1000

function toDate(value?: string | number | Date | null): Date | null {
  if (!value) return null
  const date = value instanceof Date ? value : new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function pad2(value: number): string {
  return String(value).padStart(2, '0')
}

function toShanghaiDateParts(date: Date) {
  const shanghaiDate = new Date(date.getTime() + SHANGHAI_OFFSET_MS)
  return {
    year: shanghaiDate.getUTCFullYear(),
    month: pad2(shanghaiDate.getUTCMonth() + 1),
    day: pad2(shanghaiDate.getUTCDate()),
    hour: pad2(shanghaiDate.getUTCHours()),
    minute: pad2(shanghaiDate.getUTCMinutes()),
  }
}

export function formatShanghaiDateTime(value?: string | number | Date | null) {
  const date = toDate(value)
  if (!date) return ''
  const parts = toShanghaiDateParts(date)
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`
}

export function formatShanghaiDate(value?: string | number | Date | null) {
  const date = toDate(value)
  if (!date) return ''
  const parts = toShanghaiDateParts(date)
  return `${parts.year}-${parts.month}-${parts.day}`
}
