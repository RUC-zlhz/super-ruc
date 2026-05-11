export interface PageMeta {
  page: number
  size: number
  total: number
}

export interface Paginated<T> {
  items: T[]
  meta: PageMeta
}

export interface RoleInfo {
  code: string
  scope_code?: string | null
}

export interface UserInfo {
  id: number
  display_name: string
  avatar_url?: string | null
  email?: string | null
  work_no?: string | null
  student_no?: string | null
  student_id?: number | null
  roles: RoleInfo[]
  must_change_password?: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}
