import { get, post } from '@/utils/request'

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
  score: number
  reason?: string | null
  source_name?: string | null
  source_url?: string | null
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
