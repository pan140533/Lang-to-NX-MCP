export interface Feature {
  feature_id: string
  type: 'block' | 'cylinder' | 'cone' | 'sphere' | string
  parameters: Record<string, number>
  position?: {
    type: string
    calculated_coords?: {
      x: number
      y: number
      z: number
    }
  }
  boolean_op: string
  order: number
}

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
}
