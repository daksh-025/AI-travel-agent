import { StreamingEvent, Message, ProgressUpdate } from "@/lib/types";

export interface StreamingCallbacks {
  onProgress: (progress: ProgressUpdate) => void;
  onTextChunk: (chunk: string) => void;
  onSuggestions: (suggestions: string[]) => void;
  onHotelResults?: (hotelSearch: { resultsTitle?: string; results: any[] }) => void;
  onWebResults?: (webSearch: { resultsTitle?: string; images?: Array<{ url: string; description?: string }> }) => void;
  onComplete: (finalMessage: string, metadata?: any) => void;
  onError: (error: Error) => void;
}

export class StreamingHandler {
  private eventSource: EventSource | null = null;
  private abortController: AbortController | null = null;
  private callbacks: StreamingCallbacks;
  private accumulatedText = '';

  constructor(callbacks: StreamingCallbacks) {
    this.callbacks = callbacks;
  }

  async startStreaming(
    apiUrl: string,
    requestBody: {
      message: string;
      tab_id: string;
      enable_progress?: boolean;
      streaming_speed?: string;
    },
    token: string | null,
    additionalHeaders?: HeadersInit
  ): Promise<void> {
    try {
      // Create abort controller for cancellation
      this.abortController = new AbortController();

      // Build headers
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(additionalHeaders as Record<string, string>),
      };

      // Add authorization header only if token is provided
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Create the streaming request
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          ...requestBody,
          enable_progress: true,
          streaming_speed: 'fast'
        }),
        signal: this.abortController.signal,
      });

      // Handle rate limit error (429)
      if (response.status === 429) {
        const errorData = await response.json();
        throw new Error(JSON.stringify({
          type: 'rate_limit',
          ...errorData.detail
        }));
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Check if the response is actually streaming
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('text/event-stream')) {
        // Fallback to regular JSON response
        const jsonResponse = await response.json();
        console.log('Fallback JSON response:', jsonResponse);
        this.callbacks.onComplete(jsonResponse.message, jsonResponse);
        return;
      }

      // Handle streaming response
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim() === '') continue;
          
          if (line.startsWith('data: ')) {
            const data = line.slice(6); // Remove 'data: ' prefix
            if (data.trim() === '') continue;
            
            try {
              const event: StreamingEvent = JSON.parse(data);
              this.handleEvent(event);
            } catch (error) {
              console.warn('Failed to parse SSE event:', data, error);
            }
          }
        }
      }

      // Process any remaining data in the buffer
      if (buffer.trim()) {
        const lines = buffer.split('\n');
        for (const line of lines) {
          if (line.trim() === '') continue;
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data.trim() === '') continue;
            
            try {
              const event: StreamingEvent = JSON.parse(data);
              this.handleEvent(event);
            } catch (error) {
              console.warn('Failed to parse final SSE event:', data, error);
            }
          }
        }
      }

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        // Request was cancelled, don't call onError
        console.log('Streaming request was cancelled');
        return;
      }
      this.callbacks.onError(error instanceof Error ? error : new Error('Unknown streaming error'));
    }
  }

  private handleEvent(event: StreamingEvent): void {
    switch (event.event_type) {
      case 'progress':
        if (event.progress) {
          this.callbacks.onProgress(event.progress);
        }
        break;

      case 'text_chunk':
        if (event.chunk) {
          this.accumulatedText += event.chunk.content;
          // Pass the chunk content as-is, let the UI handle formatting
          this.callbacks.onTextChunk(event.chunk.content);
        }
        break;

      case 'suggestions':
        if (event.suggestions) {
          this.callbacks.onSuggestions(event.suggestions);
        }
        break;

      case 'complete':
        console.log('Complete event received:', event);
        if (event.final_message) {
          this.callbacks.onComplete(event.final_message, event.metadata);
        } else if (this.accumulatedText) {
          // Fallback to accumulated text if no final message
          this.callbacks.onComplete(this.accumulatedText, event.metadata);
        }
        break;

      case 'hotel_results':
        if (event.hotel_search && this.callbacks.onHotelResults) {
          this.callbacks.onHotelResults(event.hotel_search);
        }
        break;

      case 'web_results':
        if (event.web_search && this.callbacks.onWebResults) {
          this.callbacks.onWebResults(event.web_search);
        }
        break;

      default:
        console.warn('Unknown event type:', event.event_type);
    }
  }

  stop(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }
}
