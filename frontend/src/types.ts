export interface ChatResponse {
  log_id?: number;
  response: string;
  complexity_label: 'LOW' | 'MEDIUM' | 'HIGH' | 'CACHED';
  complexity_score: number;
  model_used: string;
  provider: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost: number;
  savings: number;
  explanation?: Record<string, number>;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: Date;
  metadata?: ChatResponse;
}

export interface SystemStats {
  totalRequests: number;
  totalCostSaved: number;
  totalCostSpent: number;
  cacheHitCount: number;
  averageLatencyMs: number;
}
