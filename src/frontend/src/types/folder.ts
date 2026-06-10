export interface Folder {
  id: string
  name: string
  created_at: string
  user_id?: string
  paperIds?: string[]
  children?: Folder[]
}
