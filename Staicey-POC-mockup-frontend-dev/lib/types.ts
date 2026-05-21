// lib/types.ts

/**
 * Role of a message sender.
 */
export type Role = "user" | "assistant" | "system";

/**
 * Single chat message.
 */
export type Message = {
  dateSeparator: any;
  id: string;                // unique id (uuid or timestamp string)
  role: Role;                // "user" | "assistant" | "system"
  content: string;           // message text
  timestamp: string;         // ISO timestamp
  avatarUrl?: string;        // optional avatar override URL
  // optional metadata for future use (e.g. sources, attachments)
  meta?: Record<string, unknown>;
  hotelResults?: Hotel[];
  hotelResultsTitle?: string;
	hotelSearch?: any;
  suggestions?: string[];    // optional suggestion buttons
  webSearch?: any;
  // Streaming-related properties
  isStreaming?: boolean;     // whether message is currently being streamed
  streamingProgress?: ProgressUpdate; // current progress information
  progressHistory?: ProgressUpdate[]; // list of all progress updates
  finalMessage?: string;     // final complete message content
  // Deferred hotel results to show after text streaming completes
  pendingHotelResultsTitle?: string;
  pendingHotelResults?: Hotel[];
};

/**
 * Progress update from streaming API
 */
export type ProgressUpdate = {
  phase: string;
  message: string;
  percentage: number;
  details: string;
};

/**
 * Streaming event types from the API
 */
export type StreamingEvent = {
  event_type: 'progress' | 'text_chunk' | 'suggestions' | 'complete' | 'hotel_results' | 'web_results';
  timestamp: string;
  session_id: string;
  tab_id?: string;
  progress?: ProgressUpdate;
  chunk?: {
    content: string;
    is_complete_word: boolean;
    delay_ms: number;
  };
  suggestions?: string[];
  final_message?: string;
  metadata?: {
    model: string;
    history_length: number;
    tab_name_suggestion?: string;
  };
  hotel_search?: {
    resultsTitle?: string;
    results: Hotel[];
  };
  web_search?: {
    resultsTitle?: string;
    images?: Array<{ url: string; description?: string }>;
  };
};

/**
 * A chat session containing many messages.
 */
export type ChatSession = {
  id: string;                // unique chat id
  title?: string;            // optional title / summary
  messages: Message[];       // list of messages (chronological)
  createdAt?: string;        // ISO timestamp when session created
  updatedAt?: string;        // ISO timestamp when session last updated
  // additional data you may want to store (filters, tags, etc.)
  meta?: Record<string, unknown>;
};

export type Hotel = {
	id: string;
	name: string;
	rating: number;
	reviews: number;
	stars: number;
	address: string;
	phone?: string;
	features: string[];
	price: string;
	priceLabel: string;
	roomType: string;
	source: string;
	sourceUrl?: URL;
	imageUrls: string[];
	aiNote: string;
	position: { lat: number; lng: number };
  extra_prices?: any;
};

export interface ChatTab {
  tab_id: string;
  title?: string;
  session_id?: string;
  created_at?: string;
  last_activity?: string;
  message_count?: number;
  is_active?: boolean;
  is_pinned?: boolean;
  order_index?: number;
}
