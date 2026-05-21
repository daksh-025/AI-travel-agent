// app/chat/guest/page.tsx
"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import { ChatSession, Message, ProgressUpdate } from "@/lib/types";
import DateSeparator from "@/app/chat/components/DateSeparator";
import ChatMessage from "@/app/chat/components/ChatMessage";
import { Send, Square, Home, LogIn } from "lucide-react";
import { StreamingHandler } from "@/app/chat/components/StreamingHandler";
import { useUser } from "@/app/context/UserContext";
import { useRateLimit } from "@/hooks/useRateLimit";
import RateLimitBanner from "@/components/custom-components/RateLimitBanner";
import RateLimitModal from "@/components/custom-components/RateLimitModal";
import { useSignInUp } from "@/app/context/SignInUpContext";
import Image from "next/image";
import { getDefaultRateLimit } from "@/lib/constants/rateLimit";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function GuestChatPage() {
  const router = useRouter();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const streamingHandlerRef = useRef<StreamingHandler | null>(null);
  const hasAutoSentRef = useRef(false);

  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [messageLoading, setMessageLoading] = useState(false);
  const [hasText, setHasText] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [rateLimitModalOpen, setRateLimitModalOpen] = useState(false);

  // Get user context and rate limiting
  const { isAuthenticated } = useUser();
  const signInUpContext = useSignInUp();
  const { 
    rateLimitInfo, 
    canSendMessage, 
    incrementUsage, 
    getResetTimeFormatted,
    fetchRateLimit,
    getHeaders 
  } = useRateLimit(isAuthenticated);

  // If user becomes authenticated, redirect to regular chat
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/chat');
    }
  }, [isAuthenticated, router]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-send query from sessionStorage on mount
  useEffect(() => {
    if (hasAutoSentRef.current) return;
    
    const guestQuery = sessionStorage.getItem('guest_query');
    if (guestQuery) {
      hasAutoSentRef.current = true;
      sessionStorage.removeItem('guest_query');
      
      // Wait a bit for the page to render
      setTimeout(() => {
        handleSend(guestQuery);
      }, 100);
    }
  }, []);

  // Auto-grow textarea
  const auto_grow = (element: HTMLTextAreaElement) => {
    element.style.height = "5px";
    element.style.height = (element.scrollHeight) + "px";
  };

  const handleSend = async (predefinedMessage?: string) => {
    const userInput = predefinedMessage || textareaRef.current?.value.trim() || "";

    if (!userInput) return;

    // Check rate limit for guest users
    if (!isAuthenticated && !canSendMessage()) {
      setRateLimitModalOpen(true);
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userInput,
      timestamp: new Date().toISOString(),
      dateSeparator: null,
    };

    // Add user message
    setMessages(prev => [...prev, userMessage]);

    // Clear textarea
    if (!predefinedMessage && textareaRef.current) {
      textareaRef.current.value = "";
      setHasText(false);
    }

    // Create initial assistant message for streaming
    const assistantMessageId = (Date.now() + 1).toString();
    const initialAssistantMessage: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      dateSeparator: null,
      isStreaming: true,
      progressHistory: [],
    };

    // Add initial assistant message
    setMessages(prev => [...prev, initialAssistantMessage]);

    try {
      setMessageLoading(true);
      setIsStreaming(true);
      
      // Get headers for guest users
      const additionalHeaders = getHeaders();

      // Create streaming handler
      const streamingHandler = new StreamingHandler({
        onProgress: (progress: ProgressUpdate) => {
          setMessages(prevMessages => {
            return prevMessages.map(msg => {
              if (msg.id === assistantMessageId) {
                const currentHistory = msg.progressHistory || [];
                const existingIndex = currentHistory.findIndex(p => p.phase === progress.phase);
                let newHistory;
                
                if (existingIndex >= 0) {
                  newHistory = [...currentHistory];
                  newHistory[existingIndex] = progress;
                } else {
                  newHistory = [...currentHistory, progress];
                }

                return {
                  ...msg,
                  streamingProgress: progress,
                  progressHistory: newHistory,
                };
              }
              return msg;
            });
          });
        },

        onTextChunk: (chunk: string) => {
          setMessages(prevMessages => {
            return prevMessages.map(msg => {
              if (msg.id === assistantMessageId) {
                // Process chunk to add proper spacing and line breaks
                let processedChunk = chunk;
                
                // Add space before chunk if the last character of existing content is not a space
                // and the first character of chunk is not a space
                if (msg.content.length > 0 && 
                    !msg.content.endsWith(' ') && 
                    !msg.content.endsWith('\n') && 
                    !processedChunk.startsWith(' ')) {
                  processedChunk = ' ' + processedChunk;
                }
                
                // Add line break after periods (. followed by space or end of chunk)
                processedChunk = processedChunk.replace(/\.\s/g, '.\n\n');
                
                return {
                  ...msg,
                  content: msg.content + processedChunk,
                };
              }
              return msg;
            });
          });
        },

        onSuggestions: (suggestions: string[]) => {
          setMessages(prevMessages => {
            return prevMessages.map(msg => {
              if (msg.id === assistantMessageId) {
                return {
                  ...msg,
                  suggestions: suggestions,
                };
              }
              return msg;
            });
          });
        },

        onHotelResults: (hotelSearch: { resultsTitle?: string; results: any[] }) => {
          setMessages(prevMessages => {
            return prevMessages.map(msg => {
              if (msg.id === assistantMessageId) {
                return {
                  ...msg,
                  hotelSearch: hotelSearch,
                  hotelResults: hotelSearch.results,
                  hotelResultsTitle: hotelSearch.resultsTitle,
                  content: "", // Clear streaming text when hotel results appear
                };
              }
              return msg;
            });
          });
        },

        onWebResults: (webSearch: { resultsTitle?: string; images?: Array<{ url: string; description?: string }> }) => {
          setMessages(prevMessages => {
            return prevMessages.map(msg => {
              if (msg.id === assistantMessageId) {
                return {
                  ...msg,
                  webSearch: webSearch,
                };
              }
              return msg;
            });
          });
        },

        onComplete: (finalMessage: string, metadata?: any) => {
          console.log('Message complete:', finalMessage);
          setIsStreaming(false);
          streamingHandlerRef.current = null;
          
          setMessages(prevMessages => {
            return prevMessages.map(msg => {
              if (msg.id === assistantMessageId) {
                // Only set content if there are no hotel results (to avoid showing summary above hotel cards)
                const hasHotelResults = msg.hotelResults && msg.hotelResults.length > 0;
                return {
                  ...msg,
                  content: hasHotelResults ? "" : finalMessage,
                  isStreaming: false,
                  streamingProgress: undefined,
                };
              }
              return msg;
            });
          });
        },

        onError: (error: Error) => {
          console.error('Streaming error:', error);
          setIsStreaming(false);
          streamingHandlerRef.current = null;
          
          // Check if it's a rate limit error
          try {
            const errorData = JSON.parse(error.message);
            if (errorData.type === 'rate_limit') {
              setRateLimitModalOpen(true);
              fetchRateLimit();
              
              // Remove the assistant message
              setMessages(prevMessages => 
                prevMessages.filter(msg => msg.id !== assistantMessageId)
              );
              return;
            }
          } catch (e) {
            // Not a rate limit error
          }
          
          // Update the assistant message with error
          setMessages(prevMessages => {
            return prevMessages.map(msg => {
              if (msg.id === assistantMessageId) {
                return {
                  ...msg,
                  isStreaming: false,
                  content: "Sorry, I encountered an error while processing your request. Please try again.",
                  streamingProgress: undefined,
                };
              }
              return msg;
            });
          });
        }
      });

      // Store the streaming handler reference
      streamingHandlerRef.current = streamingHandler;

      // Start streaming (guest users use tab_id: "guest")
      await streamingHandler.startStreaming(
        `${API_BASE_URL}/chat/message/stream`,
        {
          message: userInput,
          tab_id: "guest",
        },
        null, // No token for guest users
        additionalHeaders
      );

      // Increment usage count for guest users after successful send
      if (!isAuthenticated) {
        incrementUsage();
      }

    } catch (err) {
      console.error('Failed to send message:', err);
      setIsStreaming(false);
      streamingHandlerRef.current = null;
      
      // Update the assistant message with error
      setMessages(prevMessages => {
        return prevMessages.map(msg => {
          if (msg.id === assistantMessageId) {
            return {
              ...msg,
              isStreaming: false,
              content: "Sorry, I encountered an error while processing your request. Please try again.",
              streamingProgress: undefined,
            };
          }
          return msg;
        });
      });
    } finally {
      setMessageLoading(false);
    }
  };

  const handleCancelStream = () => {
    if (streamingHandlerRef.current) {
      streamingHandlerRef.current.stop();
      streamingHandlerRef.current = null;
      setIsStreaming(false);
      setMessageLoading(false);
    }
  };

  const handleSignUpClick = () => {
    router.push('/');
    if (signInUpContext) {
      signInUpContext.openPopup();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#eee]">
      {/* Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Image
              src="/assets/images/logos/chat-logo.png"
              alt="Staicey"
              width={120}
              height={40}
              className="h-8 w-auto"
            />
            {/* <span className="text-sm text-gray-500 hidden sm:inline">Try it free - Sign up for unlimited access</span> */}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push('/')}
              className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100 transition-colors"
              title="Home"
            >
              <Home className="w-5 h-5" />
            </button>
            {/* <button
              onClick={handleSignUpClick}
              className="px-4 py-2 bg-[#7C3AED] text-white rounded-lg font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
            >
              <LogIn className="w-4 h-4" />
              <span className="hidden sm:inline">Sign Up / Login</span>
              <span className="sm:hidden">Login</span>
            </button> */}
          </div>
        </div>
      </div>

      {/* Rate Limit Banner */}
      <RateLimitBanner
        rateLimitInfo={rateLimitInfo}
        resetTimeFormatted={getResetTimeFormatted()}
        onSignUpClick={handleSignUpClick}
      />

      {/* Rate Limit Modal */}
      <RateLimitModal
        isOpen={rateLimitModalOpen}
        onClose={() => setRateLimitModalOpen(false)}
        onSignUp={handleSignUpClick}
        resetTimeFormatted={getResetTimeFormatted()}
      />

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-hide p-4 space-y-4 lg:px-10" style={{alignContent: "end"}}>
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <img 
              src="/assets/images/images/staicey-avatar.png" 
              alt="Staicey" 
              className="w-32 h-32 mx-auto mb-4 opacity-50"
            />
            <p className="text-lg">Ask me anything about your travel plans!</p>
            <p className="text-sm mt-2">You have {rateLimitInfo?.remaining || getDefaultRateLimit()} free searches today</p>
          </div>
        ) : (
          messages.map((msg, idx) => {
            if (msg.hotelSearch) {
              msg.hotelResultsTitle = msg.hotelSearch.resultsTitle;
              msg.hotelResults = msg.hotelSearch.results;
            }
            const prev = messages[idx - 1];
            const prevDate = prev ? prev.timestamp.split("T")[0] : null;
            const currDate = msg.timestamp.split("T")[0];
            const showDateSeparator = prevDate !== currDate;

            return (
              <div key={msg.id || `msg-${idx}`}>
                {showDateSeparator && <DateSeparator date={msg.timestamp} />}
                <ChatMessage message={msg} />
                {idx === messages.length - 1 && msg.role === "assistant" && msg.suggestions && msg.suggestions.length > 0 && (
                  <div className="flex flex-col gap-4 mt-4 mx-auto w-[92%]">
                    <div className="flex flex-col gap-3 flex-wrap">
                      {msg.suggestions.map((suggestion, index) => (
                        <button 
                          key={index}
                          className="p-3 bg-[#252d63] text-white rounded-full w-fit text-sm hover:bg-[#1a1f4a] transition-colors duration-200"
                          onClick={() => handleSend(suggestion)}
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
        
        {/* Loading Indicator */}
        {messageLoading && (
          <div className="flex items-center space-x-2 p-4 bg-transparent justify-center rounded-lg">
            <img src="/assets/images/icons/staicey-loading.gif" alt="Loading" className="w-12 h-12" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 pt-1 pb-4 flex items-center gap-2 bg-transparent relative">
        <textarea
          ref={textareaRef}
          placeholder="Talk to Staicey..."
          className="flex-1 border rounded-xl px-4 py-2 focus:outline-none max-h-[400px] min-h-[100px] disabled:bg-slate-50"
          onChange={(e) => setHasText(e.target.value.trim().length > 0)}
          onInput={(e) => auto_grow(e.target as HTMLTextAreaElement)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !isStreaming) {
              e.preventDefault();
              handleSend();
            }
          }}
          rows={1}
          disabled={loading || (!canSendMessage() && !isStreaming)}
        />
        <button
          onClick={() => {
            if (isStreaming) {
              handleCancelStream();
            } else {
              handleSend();
            }
          }}
          disabled={(!hasText && !isStreaming) || loading}
          className={`p-2 rounded-full absolute bottom-7 right-10 disabled:opacity-50 disabled:cursor-not-allowed ${
            isStreaming 
              ? "bg-red-600 text-white hover:bg-red-700" 
              : "bg-purple-600 text-white hover:bg-purple-700"
          }`}
        >
          {isStreaming ? <Square size={18} /> : <Send size={18} />}
        </button>
      </div>
    </div>
  );
}

