import http from './request'

export async function downloadFile(url: string, filename?: string, params?: Record<string, any>) {
  const resp = await http.get(url, { params, responseType: 'blob' })
  const blob = new Blob([resp.data as BlobPart])
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename || extractFilename(resp.headers?.['content-disposition']) || 'download'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(a.href)
}

function extractFilename(disposition?: string): string | null {
  if (!disposition) return null
  const match = /filename\*?=(?:UTF-8''|")?([^";]+)/i.exec(disposition)
  if (!match) return null
  try {
    return decodeURIComponent(match[1].replace(/"/g, ''))
  } catch {
    return match[1]
  }
}
