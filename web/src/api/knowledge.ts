import { get, post, patch, del } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'

export interface KnowledgeEntry {
  id: number
  code: string
  title: string
  body: string
  category?: string | null
  tags?: string[] | null
  source_url?: string | null
  is_active: boolean
  updated_at: string
}

export function listEntries(params: { q?: string; category?: string; page?: number; size?: number }) {
  return get<ApiEnvelope<Paginated<KnowledgeEntry>>>('/knowledge/entries', { params })
}

export function searchKnowledge(q: string) {
  return get<ApiEnvelope<{ entries: KnowledgeEntry[]; matched_by: string }>>(
    '/knowledge/search',
    { params: { q } },
  )
}

export function upsertEntry(payload: Partial<KnowledgeEntry>) {
  return post<ApiEnvelope<KnowledgeEntry>>('/admin/knowledge/entries', payload)
}

export function deleteEntry(id: number) {
  return del<ApiEnvelope<{ id: number }>>(`/admin/knowledge/entries/${id}`)
}
