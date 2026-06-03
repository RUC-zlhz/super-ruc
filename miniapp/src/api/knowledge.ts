import { buildApiUrl, get, getAuthHeader, post } from '@/utils/request'
import { downloadBinaryFile } from '@/utils/file'

export interface KnowledgeCategory {
  code: string
  name: string
  parent_code?: string | null
  sort_order: number
  is_active: boolean
}

export interface KnowledgeEntry {
  id: number
  slug: string
  title: string
  summary?: string | null
  category_code?: string | null
  source_name?: string | null
  source_url?: string | null
  source_is_official?: boolean
  status: string
  ambiguity_flag: boolean
  version_label?: string | null
  updated_at: string
  tags: string[]
}

export interface KnowledgeEntryDetail extends KnowledgeEntry {
  applicable_condition?: string | null
  required_materials?: string | null
  process_steps?: string | null
  body_md?: string | null
  manual_consult_hint?: string | null
  source?: {
    source_name: string
    source_url?: string | null
    is_official?: boolean
    issuing_org?: string | null
    version_label?: string | null
  } | null
  templates: {
    template_id: number
    template_name: string
    template_type: string
    version_label?: string | null
  }[]
}

export interface KnowledgeSearchParams {
  q?: string
  category?: string | null
  tag?: string | null
  page?: number
  size?: number
}

export interface SearchResult {
  items: KnowledgeEntry[]
  meta: {
    page: number
    size: number
    total: number
  }
}

export interface AiMatchCandidate {
  entry_id: number
  slug: string
  title: string
  summary?: string | null
  score: number
  reason?: string | null
  source_name?: string | null
  source_url?: string | null
  source_is_official?: boolean
  version_label?: string | null
  ambiguity_flag: boolean
}

export interface AiMatchResult {
  engine: string
  candidates: AiMatchCandidate[]
  manual_consult_required: boolean
  manual_consult_hint?: string | null
  disclaimer: string
}

export interface TemplateDownloadLink {
  template_id: number
  download_url: string
  expires_in_minutes: number
}

export interface KnowledgeTemplateItem {
  id: number
  template_name: string
  template_type: string
  category_code?: string | null
  applicable_scenario?: string | null
  version_label?: string | null
  file_size?: number | null
  mime_type?: string | null
  status: string
  uploaded_at: string
}

export interface PaginatedResult<T> {
  items: T[]
  meta: {
    page: number
    size: number
    total: number
  }
}

export function listKnowledgeCategories() {
  return get<KnowledgeCategory[]>('/knowledge/categories')
}

export function searchKnowledge(params: KnowledgeSearchParams | string) {
  return get<SearchResult>(
    '/knowledge/search',
    typeof params === 'string' ? { q: params } : params,
  )
}

export function getEntryDetail(id: number) {
  return get<KnowledgeEntryDetail>(`/knowledge/${id}`)
}

export function aiMatchKnowledge(query: string, topK = 3) {
  return post<AiMatchResult>('/knowledge/ai-match', { query, top_k: topK })
}

export function getTemplateDownloadLink(templateId: number) {
  return get<TemplateDownloadLink>(`/knowledge/templates/${templateId}/download`)
}

export function downloadTemplateFile(
  templateId: number,
  options?: {
    templateName?: string | null
    templateType?: string | null
  },
) {
  return downloadBinaryFile(`/knowledge/templates/${templateId}/file`, {
    fallbackName: options?.templateName || `template-${templateId}`,
    preferredExtension: options?.templateType?.trim().toLowerCase() || null,
  })
}

export function downloadTemplateFromUrl(url: string) {
  return new Promise<{ tempFilePath: string; statusCode: number }>((resolve, reject) => {
    uni.downloadFile({
      url: url.startsWith('http://') || url.startsWith('https://') ? url : buildApiUrl(url),
      header: getAuthHeader(),
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300 && res.tempFilePath) {
          resolve({ tempFilePath: res.tempFilePath, statusCode: res.statusCode })
          return
        }
        reject(new Error('模板下载失败'))
      },
      fail(err) {
        reject(err)
      },
    })
  })
}

export function listStudentTemplates(params?: {
  q?: string
  category?: string | null
  page?: number
  size?: number
}) {
  return get<PaginatedResult<KnowledgeTemplateItem>>('/knowledge/templates', params)
}
