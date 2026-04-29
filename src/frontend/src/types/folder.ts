export interface Folder {
  id: string
  name: string
  user_id?: string
  paperIds: string[]
  children?: Folder[]
  created_at?: string
}
