export interface ChatMessage {
  id: string
  role: 'counselor' | 'student'
  content: string
  timestamp: number
}

export interface CounselorInfo {
  name: string
  avatar: string
}

export type WsMessageType = 'info' | 'status' | 'message' | 'chunk' | 'stern_mode' | 'done' | 'error'

export interface WsPayload {
  type: WsMessageType
  content: string
  role?: 'counselor' | 'student'
  counselor_name?: string
  counselor_avatar?: string
}
