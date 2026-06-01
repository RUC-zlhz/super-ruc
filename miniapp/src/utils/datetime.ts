const SHANGHAI_TIME_ZONE = 'Asia/Shanghai'

function toDate(value?: string | number | Date | null): Date | null {
  if (!value) return null
  const date = value instanceof Date ? value : new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatShanghaiDateTime(value?: string | number | Date | null) {
  const date = toDate(value)
  if (!date) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: SHANGHAI_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date).replace(/\//g, '-')
}

export function formatShanghaiDate(value?: string | number | Date | null) {
  const date = toDate(value)
  if (!date) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: SHANGHAI_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date).replace(/\//g, '-')
}
