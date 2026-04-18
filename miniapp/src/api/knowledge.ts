import { get } from '@/utils/request'

export interface KnowledgeEntry {
  id: number
  code: string
  title: string
  body: string
  category?: string | null
  tags?: string[] | null
  source_url?: string | null
}

export interface SearchResult {
  entries: KnowledgeEntry[]
  matched_by: string
}

export function searchKnowledge(q: string) {
  return get<SearchResult>('/knowledge/search', { q })
}

export function getEntryDetail(id: number) {
  return get<KnowledgeEntry>(`/knowledge/entries/${id}`)
}
