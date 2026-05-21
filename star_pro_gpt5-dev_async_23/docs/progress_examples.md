# Progress Tracking Implementation Guide

This document provides examples of how to implement progress tracking in your frontend application using the different methods available.

## Available Endpoints

### 1. Server-Sent Events (SSE) - Recommended
**Endpoint:** `GET /chat/progress/{session_id}`
**Content-Type:** `text/event-stream`

### 2. WebSocket
**Endpoint:** `WS /chat/progress/{session_id}/ws`

### 3. HTTP Polling
**Endpoint:** `GET /chat/progress/{session_id}/status`

## Frontend Implementation Examples

### JavaScript/TypeScript - Server-Sent Events

```javascript
class ProgressTracker {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.eventSource = null;
        this.callbacks = {
            onProgress: null,
            onComplete: null,
            onError: null
        };
    }

    startTracking() {
        const url = `/chat/progress/${this.sessionId}`;
        this.eventSource = new EventSource(url);

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'progress') {
                    this.handleProgress(data.data);
                } else if (data.type === 'close') {
                    this.handleComplete();
                } else if (data.type === 'error') {
                    this.handleError(data.message);
                }
            } catch (error) {
                console.error('Error parsing SSE data:', error);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            this.handleError('Connection error');
        };
    }

    handleProgress(progressData) {
        console.log('Progress update:', progressData);
        
        // Update UI with progress information
        if (this.callbacks.onProgress) {
            this.callbacks.onProgress(progressData);
        }

        // Example UI updates:
        // - Update progress bar
        // - Show current step message
        // - Display tool being used
        // - Show estimated time remaining
    }

    handleComplete() {
        console.log('Progress tracking completed');
        if (this.callbacks.onComplete) {
            this.callbacks.onComplete();
        }
        this.stopTracking();
    }

    handleError(message) {
        console.error('Progress error:', message);
        if (this.callbacks.onError) {
            this.callbacks.onError(message);
        }
        this.stopTracking();
    }

    stopTracking() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    onProgress(callback) {
        this.callbacks.onProgress = callback;
        return this;
    }

    onComplete(callback) {
        this.callbacks.onComplete = callback;
        return this;
    }

    onError(callback) {
        this.callbacks.onError = callback;
        return this;
    }
}

// Usage example
const tracker = new ProgressTracker('your-session-id')
    .onProgress((progress) => {
        // Update progress bar
        document.getElementById('progress-bar').style.width = `${progress.progress_percentage}%`;
        
        // Update status message
        document.getElementById('status-message').textContent = progress.message;
        
        // Show current tool if available
        if (progress.current_tool) {
            document.getElementById('current-tool').textContent = 
                `Using: ${progress.current_tool.tool_name}`;
        }
    })
    .onComplete(() => {
        console.log('Chat processing completed!');
        document.getElementById('progress-container').style.display = 'none';
    })
    .onError((error) => {
        console.error('Progress error:', error);
        document.getElementById('error-message').textContent = error;
    });

// Start tracking when sending a message
function sendMessage(message) {
    tracker.startTracking();
    
    // Send your chat message
    fetch('/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            session_id: 'your-session-id'
        })
    });
}
```

### React Hook Example

```typescript
import { useState, useEffect, useCallback } from 'react';

interface ProgressData {
    session_id: string;
    current_step: string;
    status: string;
    message: string;
    progress_percentage: number;
    tools_used: string[];
    current_tool?: {
        tool_name: string;
        status: string;
        message: string;
        progress_percentage?: number;
    };
    estimated_time_remaining?: number;
}

export const useProgressTracking = (sessionId: string) => {
    const [progress, setProgress] = useState<ProgressData | null>(null);
    const [isTracking, setIsTracking] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const startTracking = useCallback(() => {
        if (!sessionId) return;

        setIsTracking(true);
        setError(null);
        
        const eventSource = new EventSource(`/chat/progress/${sessionId}`);
        
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'progress') {
                    setProgress(data.data);
                } else if (data.type === 'close') {
                    setIsTracking(false);
                    eventSource.close();
                }
            } catch (err) {
                setError('Failed to parse progress data');
            }
        };

        eventSource.onerror = () => {
            setError('Connection lost');
            setIsTracking(false);
            eventSource.close();
        };

        return () => {
            eventSource.close();
            setIsTracking(false);
        };
    }, [sessionId]);

    return {
        progress,
        isTracking,
        error,
        startTracking
    };
};

// Usage in component
const ChatComponent = () => {
    const { progress, isTracking, error, startTracking } = useProgressTracking(sessionId);

    const sendMessage = async (message: string) => {
        // Start tracking progress
        const stopTracking = startTracking();
        
        try {
            const response = await fetch('/chat/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, session_id: sessionId })
            });
            
            const result = await response.json();
            // Handle response
        } catch (err) {
            console.error('Error sending message:', err);
        } finally {
            // Stop tracking when done
            if (stopTracking) stopTracking();
        }
    };

    return (
        <div>
            {isTracking && (
                <div className="progress-container">
                    <div className="progress-bar">
                        <div 
                            className="progress-fill" 
                            style={{ width: `${progress?.progress_percentage || 0}%` }}
                        />
                    </div>
                    <div className="status-message">
                        {progress?.message || 'Processing...'}
                    </div>
                    {progress?.current_tool && (
                        <div className="current-tool">
                            Using: {progress.current_tool.tool_name}
                        </div>
                    )}
                </div>
            )}
            {error && <div className="error">{error}</div>}
        </div>
    );
};
```

### WebSocket Implementation

```javascript
class WebSocketProgressTracker {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.ws = null;
        this.callbacks = {
            onProgress: null,
            onComplete: null,
            onError: null
        };
    }

    connect() {
        const wsUrl = `ws://localhost:8000/chat/progress/${this.sessionId}/ws`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            // Subscribe to progress updates
            this.ws.send(JSON.stringify({ type: 'subscribe' }));
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'progress') {
                    this.handleProgress(data.data);
                } else if (data.type === 'complete') {
                    this.handleComplete();
                } else if (data.type === 'error') {
                    this.handleError(data.message);
                } else if (data.type === 'pong') {
                    // Handle ping-pong for connection health
                    console.log('Received pong');
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.handleError('WebSocket connection error');
        };

        this.ws.onclose = () => {
            console.log('WebSocket connection closed');
        };
    }

    handleProgress(progressData) {
        if (this.callbacks.onProgress) {
            this.callbacks.onProgress(progressData);
        }
    }

    handleComplete() {
        if (this.callbacks.onComplete) {
            this.callbacks.onComplete();
        }
        this.disconnect();
    }

    handleError(message) {
        if (this.callbacks.onError) {
            this.callbacks.onError(message);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    ping() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping' }));
        }
    }

    onProgress(callback) {
        this.callbacks.onProgress = callback;
        return this;
    }

    onComplete(callback) {
        this.callbacks.onComplete = callback;
        return this;
    }

    onError(callback) {
        this.callbacks.onError = callback;
        return this;
    }
}
```

### HTTP Polling Implementation

```javascript
class PollingProgressTracker {
    constructor(sessionId, interval = 1000) {
        this.sessionId = sessionId;
        this.interval = interval;
        this.pollingInterval = null;
        this.callbacks = {
            onProgress: null,
            onComplete: null,
            onError: null
        };
    }

    startPolling() {
        this.pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/chat/progress/${this.sessionId}/status`);
                const data = await response.json();
                
                if (data.progress) {
                    this.handleProgress(data.progress);
                    
                    // Stop polling if completed
                    if (data.progress.status === 'completed' || data.progress.status === 'error') {
                        this.stopPolling();
                        if (data.progress.status === 'completed') {
                            this.handleComplete();
                        } else {
                            this.handleError(data.progress.message);
                        }
                    }
                }
            } catch (error) {
                console.error('Polling error:', error);
                this.handleError('Failed to fetch progress');
                this.stopPolling();
            }
        }, this.interval);
    }

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    handleProgress(progressData) {
        if (this.callbacks.onProgress) {
            this.callbacks.onProgress(progressData);
        }
    }

    handleComplete() {
        if (this.callbacks.onComplete) {
            this.callbacks.onComplete();
        }
    }

    handleError(message) {
        if (this.callbacks.onError) {
            this.callbacks.onError(message);
        }
    }

    onProgress(callback) {
        this.callbacks.onProgress = callback;
        return this;
    }

    onComplete(callback) {
        this.callbacks.onComplete = callback;
        return this;
    }

    onError(callback) {
        this.callbacks.onError = callback;
        return this;
    }
}
```

## Progress Data Structure

The progress data follows this structure:

```typescript
interface ChatProgress {
    session_id: string;
    current_step: string;           // "initializing", "preparing", "processing", "finalizing"
    status: ProgressStatus;         // "starting", "thinking", "searching", "processing", "finalizing", "completed", "error"
    message: string;                // Human-readable status message
    progress_percentage: number;    // 0-100
    tools_used: string[];          // List of tools that have been used
    current_tool?: ToolProgress;   // Details about currently running tool
    estimated_time_remaining?: number; // Estimated seconds remaining
    timestamp: string;             // ISO timestamp
}

interface ToolProgress {
    tool_name: string;             // Name of the tool
    status: string;                // "starting", "in_progress", "completed", "error"
    message: string;               // Tool-specific message
    progress_percentage?: number;  // Tool-specific progress
    start_time?: string;           // When tool started
    end_time?: string;             // When tool completed
    result_preview?: string;       // Preview of tool result
}
```

## Recommendations

1. **Use Server-Sent Events (SSE)** for most cases - it's simpler and more reliable than WebSockets for one-way progress updates
2. **Use WebSockets** if you need bidirectional communication or more control over the connection
3. **Use HTTP Polling** as a fallback when SSE/WebSockets aren't available or for simple implementations
4. **Always handle errors gracefully** - connections can drop, and progress tracking should be resilient
5. **Implement proper cleanup** - close connections and clear intervals when components unmount
6. **Show meaningful progress information** - users appreciate knowing what the AI is doing, especially for longer operations

## Integration with Your Chat Flow

1. When user sends a message, start progress tracking
2. Show progress bar and status message
3. Update UI as progress events arrive
4. Hide progress indicator when completed
5. Handle errors gracefully
6. Clean up connections when done
