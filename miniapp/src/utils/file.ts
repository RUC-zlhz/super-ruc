import { AuthRequiredError, buildApiUrl, getAuthHeader, handleUnauthorized, hasToken } from '@/utils/request'

export interface DownloadedFileResult {
  fileName: string
  filePath: string
  statusCode: number
  contentType?: string | null
}

type BinaryDownloadOptions = {
  fallbackName?: string | null
  params?: Record<string, any>
  preferredExtension?: string | null
}

type BinaryResponse = {
  statusCode: number
  data: ArrayBuffer | string
  header?: Record<string, unknown>
  headers?: Record<string, unknown>
}

const FILE_NAME_SANITIZE_PATTERN = /[\\/:*?"<>|\r\n]+/g

function normalizeHeaders(rawHeaders?: Record<string, unknown> | null): Record<string, string> {
  if (!rawHeaders) return {}
  const normalized: Record<string, string> = {}
  for (const [key, value] of Object.entries(rawHeaders)) {
    normalized[key.toLowerCase()] = String(value ?? '')
  }
  return normalized
}

function parseContentDispositionFilename(contentDisposition: string) {
  if (!contentDisposition) return null

  const utf8Match = /filename\*=UTF-8''([^;]+)/i.exec(contentDisposition)
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1].trim())
    } catch {
      return utf8Match[1].trim()
    }
  }

  const quotedMatch = /filename="([^"]+)"/i.exec(contentDisposition)
  if (quotedMatch?.[1]) return quotedMatch[1].trim()

  const plainMatch = /filename=([^;]+)/i.exec(contentDisposition)
  if (plainMatch?.[1]) {
    return plainMatch[1].trim().replace(/^"(.*)"$/, '$1')
  }

  return null
}

function guessExtensionFromContentType(contentType?: string | null) {
  const normalized = (contentType || '').toLowerCase()
  if (!normalized) return null
  if (normalized.includes('pdf')) return 'pdf'
  if (normalized.includes('officedocument.wordprocessingml.document')) return 'docx'
  if (normalized.includes('msword')) return 'doc'
  if (normalized.includes('officedocument.spreadsheetml.sheet')) return 'xlsx'
  if (normalized.includes('ms-excel')) return 'xls'
  if (normalized.includes('presentationml.presentation')) return 'pptx'
  if (normalized.includes('ms-powerpoint')) return 'ppt'
  if (normalized.includes('text/csv')) return 'csv'
  if (normalized.includes('text/plain')) return 'txt'
  return null
}

function sanitizeFileName(fileName: string) {
  const cleaned = fileName.trim().replace(FILE_NAME_SANITIZE_PATTERN, '_')
  return cleaned || 'template-download'
}

function ensureFileExtension(fileName: string, preferredExtension?: string | null) {
  const normalized = sanitizeFileName(fileName)
  if (/\.[A-Za-z0-9]+$/.test(normalized) || !preferredExtension) return normalized
  return `${normalized}.${preferredExtension.replace(/^\./, '')}`
}

function getUserDataPath() {
  const wxRuntime = (globalThis as { wx?: { env?: { USER_DATA_PATH?: string } } }).wx
  return wxRuntime?.env?.USER_DATA_PATH || null
}

function getFileSystemManager() {
  const wxRuntime = (globalThis as { wx?: { getFileSystemManager?: () => any } }).wx
  if (typeof wxRuntime?.getFileSystemManager === 'function') {
    return wxRuntime.getFileSystemManager()
  }
  return null
}

function writeBinaryToLocalFile(filePath: string, data: ArrayBuffer) {
  return new Promise<string>((resolve, reject) => {
    const fileSystemManager = getFileSystemManager()
    if (!fileSystemManager) {
      reject(new Error('当前环境不支持文件下载'))
      return
    }
    fileSystemManager.writeFile({
      filePath,
      data,
      success: () => resolve(filePath),
      fail: () => reject(new Error('模板文件保存失败，请稍后重试')),
    })
  })
}

function decodeArrayBufferToText(data: ArrayBuffer) {
  try {
    return new TextDecoder('utf-8').decode(new Uint8Array(data))
  } catch {
    const chars = Array.from(new Uint8Array(data)).map((item) => String.fromCharCode(item))
    return chars.join('')
  }
}

function parseBinaryErrorMessage(response: BinaryResponse, fallback: string) {
  const rawText = typeof response.data === 'string'
    ? response.data
    : decodeArrayBufferToText(response.data)

  if (rawText.trim()) {
    try {
      const payload = JSON.parse(rawText) as { message?: unknown }
      if (typeof payload.message === 'string' && payload.message.trim()) {
        return payload.message.trim()
      }
    } catch {
      return rawText.trim()
    }
  }
  return fallback
}

export function downloadBinaryFile(
  url: string,
  options: BinaryDownloadOptions = {},
): Promise<DownloadedFileResult> {
  return new Promise((resolve, reject) => {
    if (!hasToken()) {
      handleUnauthorized(true)
      reject(new AuthRequiredError())
      return
    }

    uni.request({
      url: buildApiUrl(url, options.params),
      method: 'GET',
      responseType: 'arraybuffer',
      header: {
        Accept: 'application/octet-stream,application/pdf,*/*',
        ...getAuthHeader(),
      },
      success: async (rawResponse) => {
        const response = rawResponse as unknown as BinaryResponse
        if (response.statusCode === 401) {
          handleUnauthorized(true)
          reject(new Error('登录已失效'))
          return
        }
        if (response.statusCode < 200 || response.statusCode >= 300) {
          reject(new Error(parseBinaryErrorMessage(response, '模板下载失败')))
          return
        }
        if (!(response.data instanceof ArrayBuffer)) {
          reject(new Error('模板下载失败，返回内容格式不正确'))
          return
        }

        const headers = normalizeHeaders(response.header || response.headers)
        const contentDisposition = headers['content-disposition'] || ''
        const contentType = headers['content-type'] || null
        const fileName = ensureFileExtension(
          parseContentDispositionFilename(contentDisposition)
            || options.fallbackName
            || 'template-download',
          options.preferredExtension || guessExtensionFromContentType(contentType),
        )

        const userDataPath = getUserDataPath()
        if (!userDataPath) {
          reject(new Error('当前环境不支持文件保存'))
          return
        }

        const filePath = `${userDataPath}/sip-template-${Date.now()}-${fileName}`

        try {
          const savedPath = await writeBinaryToLocalFile(filePath, response.data)
          resolve({
            fileName,
            filePath: savedPath,
            statusCode: response.statusCode,
            contentType,
          })
        } catch (error) {
          reject(error instanceof Error ? error : new Error('模板文件保存失败，请稍后重试'))
        }
      },
      fail: () => {
        reject(new Error('网络异常，请稍后重试'))
      },
    })
  })
}

export function saveFileToDiskIfSupported(filePath: string): Promise<boolean> {
  const wxRuntime = (globalThis as {
    wx?: {
      saveFileToDisk?: (options: {
        filePath: string
        success?: () => void
        fail?: (error?: { errMsg?: string }) => void
      }) => void
    }
  }).wx

  if (typeof wxRuntime?.saveFileToDisk !== 'function') {
    return Promise.resolve(false)
  }
  const saveFileToDisk = wxRuntime.saveFileToDisk

  return new Promise((resolve, reject) => {
    saveFileToDisk({
      filePath,
      success: () => resolve(true),
      fail: (error) => {
        const errorMessage = error?.errMsg || ''
        if (errorMessage.includes('cancel')) {
          resolve(false)
          return
        }
        reject(new Error('文件已下载，但保存到系统失败'))
      },
    })
  })
}
