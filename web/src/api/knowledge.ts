import { get, post, patch, del } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'

export type KnowledgeEntryStatus = 'DRAFT' | 'PUBLISHED' | 'DEPRECATED'
export type TemplateStatus = 'ACTIVE' | 'DEPRECATED'

export interface KnowledgeSource {
  id: number
  source_name: string
  source_url?: string | null
  issuing_org?: string | null
  version_label?: string | null
  effective_date?: string | null
  expires_on?: string | null
  is_official: boolean
  is_active: boolean
  updated_at: string
}

export interface KnowledgeTemplate {
  id: number
  template_name: string
  template_type: string
  category_code?: string | null
  applicable_scenario?: string | null
  version_label?: string | null
  tags: string[]
  file_size?: number | null
  mime_type?: string | null
  status: TemplateStatus
  uploaded_at: string
}

export interface TemplateDownloadLink {
  template_id: number
  download_url: string
  expires_in_minutes: number
}

export interface KnowledgeEntryBrief {
  id: number
  slug: string
  title: string
  summary?: string | null
  category_code?: string | null
  status: KnowledgeEntryStatus
  ambiguity_flag: boolean
  version_label?: string | null
  updated_at: string
  tags: string[]
  source_name?: string | null
  source_url?: string | null
  source_is_official: boolean
}

export interface KnowledgeEntryDetail extends KnowledgeEntryBrief {
  applicable_condition?: string | null
  required_materials?: string | null
  process_steps?: string | null
  body_md?: string | null
  manual_consult_hint?: string | null
  published_at?: string | null
  source?: KnowledgeSource | null
  templates: Array<{
    template_id: number
    template_name: string
    template_type: string
    version_label?: string | null
  }>
}

export interface KnowledgeRevision {
  id: number
  action: string
  version_label?: string | null
  status_before?: string | null
  status_after?: string | null
  operator_id?: number | null
  operator_role?: string | null
  note?: string | null
  occurred_at: string
}

export interface EntryPayload {
  slug?: string
  title?: string
  summary?: string | null
  category_code?: string | null
  applicable_condition?: string | null
  required_materials?: string | null
  process_steps?: string | null
  body_md?: string | null
  source_id?: number | null
  version_label?: string | null
  ambiguity_flag?: boolean
  manual_consult_hint?: string | null
  tags?: string[]
  template_ids?: number[]
}

export function listEntries(params: { q?: string; status?: string; page?: number; size?: number }) {
  return get<ApiEnvelope<Paginated<KnowledgeEntryBrief>>>('/admin/knowledge/entries', { params })
}

export function createEntry(payload: EntryPayload) {
  return post<ApiEnvelope<KnowledgeEntryDetail>>('/admin/knowledge/entries', payload)
}

export function getEntry(id: number) {
  return get<ApiEnvelope<KnowledgeEntryDetail>>(`/admin/knowledge/entries/${id}`)
}

export function updateEntry(id: number, payload: EntryPayload) {
  return patch<ApiEnvelope<KnowledgeEntryDetail>>(`/admin/knowledge/entries/${id}`, payload)
}

export function publishEntry(id: number, note?: string) {
  return post<ApiEnvelope<KnowledgeEntryDetail>>(`/admin/knowledge/entries/${id}/publish`, { note })
}

export function deprecateEntry(id: number, note?: string) {
  return post<ApiEnvelope<KnowledgeEntryDetail>>(`/admin/knowledge/entries/${id}/deprecate`, { note })
}

export function listEntryRevisions(id: number) {
  return get<ApiEnvelope<KnowledgeRevision[]>>(`/admin/knowledge/entries/${id}/revisions`)
}

export function listSources(includeInactive = false) {
  return get<ApiEnvelope<KnowledgeSource[]>>('/admin/knowledge/sources', {
    params: { include_inactive: includeInactive },
  })
}

export function createSource(payload: {
  source_name: string
  source_url?: string | null
  issuing_org?: string | null
  version_label?: string | null
  effective_date?: string | null
  expires_on?: string | null
  is_official?: boolean
}) {
  return post<ApiEnvelope<KnowledgeSource>>('/admin/knowledge/sources', payload)
}

export function updateSource(
  id: number,
  payload: {
    source_name?: string
    source_url?: string | null
    issuing_org?: string | null
    version_label?: string | null
    effective_date?: string | null
    expires_on?: string | null
    is_official?: boolean
    is_active?: boolean
  },
) {
  return patch<ApiEnvelope<KnowledgeSource>>(`/admin/knowledge/sources/${id}`, payload)
}

export function listTemplates(params: {
  q?: string
  category?: string
  include_deprecated?: boolean
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<KnowledgeTemplate>>>('/admin/knowledge/templates', { params })
}

export function uploadTemplate(payload: {
  file: File
  template_name: string
  template_type: string
  category_code?: string | null
  applicable_scenario?: string | null
  version_label?: string | null
  tags?: string[]
}) {
  const body = new FormData()
  body.append('file', payload.file)
  body.append('template_name', payload.template_name)
  body.append('template_type', payload.template_type)
  if (payload.category_code) body.append('category_code', payload.category_code)
  if (payload.applicable_scenario) body.append('applicable_scenario', payload.applicable_scenario)
  if (payload.version_label) body.append('version_label', payload.version_label)
  if (payload.tags?.length) body.append('tags', JSON.stringify(payload.tags))
  return post<ApiEnvelope<KnowledgeTemplate>>('/admin/knowledge/templates', body, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getTemplateDownloadLink(
  templateId: number,
  scope: 'student' | 'admin' = 'student',
) {
  const path = scope === 'admin'
    ? `/admin/knowledge/templates/${templateId}/download`
    : `/knowledge/templates/${templateId}/download`
  return get<ApiEnvelope<TemplateDownloadLink>>(path)
}

export function deprecateTemplate(id: number) {
  return del<ApiEnvelope<KnowledgeTemplate>>(`/admin/knowledge/templates/${id}`)
}
