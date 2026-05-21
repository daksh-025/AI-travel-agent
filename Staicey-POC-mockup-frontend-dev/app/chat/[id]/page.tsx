// app/chat/[id]/page.tsx
"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import { ChatSession, ChatTab, Message, ProgressUpdate } from "@/lib/types";
import DateSeparator from "@/app/chat/components/DateSeparator";
import ChatMessage from "@/app/chat/components/ChatMessage";
import Sidebar from "@/components/custom-components/Sidebar";
import SidebarMobile from "@/components/custom-components/SidebarMobile";
import { Send, Square } from "lucide-react";
import { StreamingHandler } from "@/app/chat/components/StreamingHandler";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function ChatPageContent() {
  const params = useParams();
  const router = useRouter();
  const chatId = params.id as string;
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isLoadingRef = useRef(false);

  const [chat, setChat] = useState<ChatSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [messageLoading, setMessageLoading] = useState(false);
//   const [chats, setChats] = useState<ChatSession[]>([]);
  const [tabs, setTabs] = useState<ChatTab[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasText, setHasText] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const streamingHandlerRef = useRef<StreamingHandler | null>(null);

  // Random loading messages
  const loadingMessages = [
    "Hold tight while I scan the skies, surf the databases, and politely interrogate some booking systems. I'll be back faster than you can say 'poolside mojito.'",
    "Crunching the numbers, cross-checking the vibes… Just a sec while I track down the top contenders for your getaway goals",
    "Give me a sec — I'm diving headfirst into my accommodation vault like Scrooge McDuck, but with better recommendations.",
    "Hold on while I scan the skies, surf the databases, and politely interrogate some booking systems.",
    "I'm on it! Just a moment while I dive into my accommodation vault and pull out the best options for your getaway goals.",
    "Hold on while I check my accommodation vault for the best options.",
    "Just a moment while I scour the skies and databases for the best options.",
  ];

  const getRandomLoadingMessage = () => {
    return loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
  };

  // Reusable function to handle 401 errors
  const handleUnauthorized = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('user_data');
    router.push('/');
  };

  // Fetch chat tabs from API
  const fetchChatTabs = async () => {
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/chat/tabs`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const tabsData: ChatTab[] = await response.json();

      // Filter out invalid tabs and ensure required fields exist
      const validTabs = tabsData.filter(tab => tab && tab.tab_id && typeof tab.tab_id === 'string');

      if (validTabs.length !== tabsData.length) {
        console.warn('Some chat tabs were filtered out due to missing tab_id:', tabsData);
      }

      setTabs(validTabs);

      // Find the current chat tab
      const currentTab = validTabs.find(tab => tab.tab_id === chatId);
      if (!currentTab) {
        throw new Error(`Chat with ID ${chatId} not found`);
      }

      const sessionId = currentTab.session_id;

      return sessionId;
    } catch (err) {
      console.error('Failed to fetch chat tabs:', err);
      setError(err instanceof Error ? err.message : 'Failed to load chats');
    }
  };

  // Auto-scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chat?.messages]);

  // Auto-focus textarea after chat loads
  useEffect(() => {
    if (!loading && !error && chat) {
      // Small delay to ensure the textarea is rendered
      const timer = setTimeout(() => {
        textareaRef.current?.focus();
      }, 100);
      
      return () => clearTimeout(timer);
    }
  }, [loading, error, chat]);

  // Retry function to reload chat data
  const retryLoadChat = async () => {
    setLoading(true);
    setError(null);
    isLoadingRef.current = false; // Reset the loading ref to allow retry
    
    try {
      const sessionId = await fetchChatTabs();
      if (!sessionId) return;

      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      if (!token) {
        setError('Authentication required');
        setLoading(false);
        return;
      }

      // Fetch chat history for this specific chat
      const response = await fetch(`${API_BASE_URL}/chat/history/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 401) {
        // Unauthorized - logout and redirect
        handleUnauthorized();
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const chatHistory = await response.json();
      
      // Random welcome messages
      const welcomeMessages = [
        "Hey hey! I'm Staicey, your AI travel buddy. No passport needed to get started — just tell me where we're going and I'll work my magic.",
        "Hi! I'm Staicey — part travel agent, part fairy godmother, minus the wand (but still pretty magical). Where to?",
        "Ready to make your inbox jealous with beautiful travel options? I'm Staicey, your pixel-powered planner. Hit me with your dream trip!",
        "Hey traveller! I'm Staicey — your shortcut to stress-free adventures. Tell me where we're headed, and I'll handle the magic carpet part.",
        "Hi, I'm Staicey — your AI compass with a sense of humor. Drop me a destination, and let's chart some memories.",
        "Welcome aboard! I'm Staicey — the kind of travel buddy who packs spreadsheets and fairy dust. Where to first?",
        "Hola, bonjour, hello! I'm Staicey — one AI, infinite travel daydreams. Where shall we spin the globe today?",
        "Nice to meet you! I'm Staicey — like Google Hotels, but sassier and way more fun. Where's our next pin drop?",
        "Hey hey! I'm Staicey — I don't do jet lag, but I do world-class trip planning. What's our first stop?",
        "All aboard! I'm Staicey — your AI conductor of adventures. Where are we riding off to today?",
        "Hi there! I'm Staicey — think of me as your digital genie, but instead of three wishes, you get unlimited trips. Where to?",
        "Greetings, traveller! I'm Staicey — I never overpack and always find the best routes. What destination's calling you?",
        "Hey you! I'm Staicey — half travel guru, half stand-up comic, fully ready to book your next getaway. Where shall we fly?",
        "Hi! I'm Staicey — I speak fluent wanderlust. Just say the word, and I'll do the travel math for you.",
        "Hello adventurer! I'm Staicey — more reliable than weather forecasts and way more fun. Where are we off to?",
        "Hey hey! I'm Staicey — let's skip the boring and head straight to the postcard-worthy. Where's our next toast happening?",
        "Hi! I'm Staicey — your travel buddy who never forgets sunscreen or snacks. What's the plan?",
        "Hello explorer! I'm Staicey — the AI that trades Monday blues for ocean views. Where are we setting sail?",
        "Hey there! I'm Staicey — I bring the charm, you bring the wanderlust. Together, we'll find your perfect trip.",
        "Hi! I'm Staicey — I turn travel dreams into checklists and check-ins. Where's your heart flying today?",
        "What's up! I'm Staicey — lighter than a carry-on, sharper than a Swiss army knife. Where are we dropping in?",
        "Hello! I'm Staicey — part concierge, part comedian, 100% ready to wow your inbox. Where to first?",
        "Hi traveller! I'm Staicey — your chill navigator with a flair for fun. Drop me a destination, and let's make waves.",
      ];
      
      // Randomly select a welcome message
      const randomWelcomeMessage = welcomeMessages[Math.floor(Math.random() * welcomeMessages.length)];

      // Create chat session with the fetched history
      const chatData: ChatSession = {
        id: chatId,
        title: `Chat ${chatId}`, // You might want to fetch the title from tabs API
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        messages: chatHistory.messages.length > 0 ? chatHistory.messages : [
          {
            id: '1',
            role: 'assistant',
            content: randomWelcomeMessage,
            timestamp: new Date().toISOString(),
            dateSeparator: null,
          }
        ],
      };
      
      setChat(chatData);
    } catch (err) {
      console.error('Failed to load chat data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load chat');
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
    }
  };

  // Fetch chat data on component mount
  useEffect(() => {
    const loadChatData = async () => {
      // Prevent duplicate calls in React Strict Mode
      if (isLoadingRef.current) return;
      
      isLoadingRef.current = true;
      const sessionId = await fetchChatTabs();
      setLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
        if (!token) {
          setError('Authentication required');
          setLoading(false);
          return;
        }

        // console.log(sessionId)
        // Fetch chat history for this specific chat
        const response = await fetch(`${API_BASE_URL}/chat/history/${sessionId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.status === 401) {
          // Unauthorized - logout and redirect
          handleUnauthorized();
          return;
        }

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const chatHistory = await response.json();
        
        // Random welcome messages
        const welcomeMessages = [
          "Hey hey! I'm Staicey, your AI travel buddy. No passport needed to get started — just tell me where we're going and I'll work my magic.",
          "Hi! I'm Staicey — part travel agent, part fairy godmother, minus the wand (but still pretty magical). Where to?",
          "Ready to make your inbox jealous with beautiful travel options? I'm Staicey, your pixel-powered planner. Hit me with your dream trip!",
          "Hey traveller! I'm Staicey — your shortcut to stress-free adventures. Tell me where we're headed, and I'll handle the magic carpet part.",
          "Hi, I'm Staicey — your AI compass with a sense of humor. Drop me a destination, and let's chart some memories.",
          "Welcome aboard! I'm Staicey — the kind of travel buddy who packs spreadsheets and fairy dust. Where to first?",
          "Hola, bonjour, hello! I'm Staicey — one AI, infinite travel daydreams. Where shall we spin the globe today?",
          "Nice to meet you! I'm Staicey — like Google Hotels, but sassier and way more fun. Where's our next pin drop?",
          "Hey hey! I'm Staicey — I don't do jet lag, but I do world-class trip planning. What's our first stop?",
          "All aboard! I'm Staicey — your AI conductor of adventures. Where are we riding off to today?",
          "Hi there! I'm Staicey — think of me as your digital genie, but instead of three wishes, you get unlimited trips. Where to?",
          "Greetings, traveller! I'm Staicey — I never overpack and always find the best routes. What destination's calling you?",
          "Hey you! I'm Staicey — half travel guru, half stand-up comic, fully ready to book your next getaway. Where shall we fly?",
          "Hi! I'm Staicey — I speak fluent wanderlust. Just say the word, and I'll do the travel math for you.",
          "Hello adventurer! I'm Staicey — more reliable than weather forecasts and way more fun. Where are we off to?",
          "Hey hey! I'm Staicey — let's skip the boring and head straight to the postcard-worthy. Where's our next toast happening?",
          "Hi! I'm Staicey — your travel buddy who never forgets sunscreen or snacks. What's the plan?",
          "Hello explorer! I'm Staicey — the AI that trades Monday blues for ocean views. Where are we setting sail?",
          "Hey there! I'm Staicey — I bring the charm, you bring the wanderlust. Together, we'll find your perfect trip.",
          "Hi! I'm Staicey — I turn travel dreams into checklists and check-ins. Where's your heart flying today?",
          "What's up! I'm Staicey — lighter than a carry-on, sharper than a Swiss army knife. Where are we dropping in?",
          "Hello! I'm Staicey — part concierge, part comedian, 100% ready to wow your inbox. Where to first?",
          "Hi traveller! I'm Staicey — your chill navigator with a flair for fun. Drop me a destination, and let's make waves.",
        ];
        
        // Randomly select a welcome message
        const randomWelcomeMessage = welcomeMessages[Math.floor(Math.random() * welcomeMessages.length)];

        // Create chat session with the fetched history
        const chatData: ChatSession = {
          id: chatId,
          title: `Chat ${chatId}`, // You might want to fetch the title from tabs API
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          messages: chatHistory.messages.length > 0 ? chatHistory.messages : [
            {
              id: '1',
              role: 'assistant',
              content: randomWelcomeMessage,
              timestamp: new Date().toISOString(),
              dateSeparator: null,
            }
          ],
        };
        
        setChat(chatData);
      } catch (err) {
        console.error('Failed to load chat data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load chat');
      } finally {
        setLoading(false);
        isLoadingRef.current = false;
      }
    };

    loadChatData();
  }, [chatId]);

  const handleNewChat = async () => {
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/chat/tabs`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: "New Chat",
        }),
      });

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const newTab: ChatTab = await response.json();
      
      // Add new tab to tabs state
      setTabs(prev => [newTab, ...prev]);
      
      // Convert to ChatSession and add to chats state
    //   const newChat: ChatSession = {
    //     id: newTab.tab_id,
    //     title: newTab.title,
    //     createdAt: newTab.created_at,
    //     updatedAt: newTab.last_activity,
    //     messages: [],
    //   };
      
    //   setChats(prev => [newChat, ...prev]);
      
      // Navigate to the new chat
      router.push(`/chat/${newTab.tab_id}`);
    } catch (err) {
      console.error('Failed to create new chat:', err);
      setError(err instanceof Error ? err.message : 'Failed to create new chat');
    }
  };

  const handleDeleteChat = async (chatId: string) => {
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      if (!token) {
        setError('Authentication required');
        handleUnauthorized();
        return;
      }

      const response = await fetch(`${API_BASE_URL}/chat/tabs/${chatId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Remove from both tabs and chats states
      setTabs(prev => prev.filter(tab => tab.tab_id !== chatId));
    //   setChats(prev => prev.filter(chat => chat.id !== chatId));
      
      // If we're deleting the current chat, redirect to main chat page
      if (chat?.id === chatId) {
        router.push('/chat');
      }
    } catch (err) {
      console.error('Failed to delete chat:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete chat');
    }
  };

  const handleClearAll = async () => {
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      if (!token) {
        setError('Authentication required');
        handleUnauthorized();
        return;
      }

      const response = await fetch(`${API_BASE_URL}/chat/history/user/all`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Clear all chats from state and redirect to main chat page
      setTabs([]);
      router.push('/chat');
    } catch (err) {
      console.error('Failed to clear all chats:', err);
      setError(err instanceof Error ? err.message : 'Failed to clear all chats');
    }
  };

  const handleCancelStream = async () => {
    try {
      // First, stop the streaming handler (this will abort the fetch request)
      if (streamingHandlerRef.current) {
        streamingHandlerRef.current.stop();
        streamingHandlerRef.current = null;
      }

      // Send cancellation request to server
      // Note: This endpoint should be implemented on the server to properly stop streaming processes
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      if (token) {
        try {
          await fetch(`${API_BASE_URL}/chat/message/cancel`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              tab_id: chatId,
              reason: 'user_cancelled',
              timestamp: new Date().toISOString()
            }),
          });
        } catch (cancelError) {
          console.warn('Failed to send cancellation request to server:', cancelError);
          // Continue with client-side cancellation even if server request fails
        }
      }

      setIsStreaming(false);
      setMessageLoading(false);
      
      // Update the last assistant message to show it was cancelled
      setChat(prevChat => {
        if (!prevChat) return prevChat;
        const messages = [...prevChat.messages];
        const lastMessage = messages[messages.length - 1];
        if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
          lastMessage.isStreaming = false;
          lastMessage.content = lastMessage.content || "Request cancelled by user.";
          lastMessage.streamingProgress = undefined;
        }
        return {
          ...prevChat,
          messages,
          updatedAt: new Date().toISOString()
        };
      });
    } catch (error) {
      console.error('Error during cancellation:', error);
      // Still reset the UI state even if cancellation fails
      setIsStreaming(false);
      setMessageLoading(false);
      if (streamingHandlerRef.current) {
        streamingHandlerRef.current = null;
      }
    }
  };

  const handleSend = async (suggestion?: string) => {
    const userInput = suggestion ? suggestion : new String(textareaRef.current?.value || "").trim();

    if (!userInput || !chat) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userInput,
      timestamp: new Date().toISOString(),
      dateSeparator: null,
    };

    // Add user message to chat immediately
    setChat(prevChat => {
      if (!prevChat) {
        return {
          id: chatId,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          messages: [userMessage]
        };
      }
      return {
        ...prevChat,
        messages: [...prevChat.messages, userMessage],
        updatedAt: new Date().toISOString()
      };
    });

    // Clear textarea using ref
    if (!suggestion && textareaRef.current) {
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
    setChat(prevChat => {
      if (!prevChat) return prevChat;
      return {
        ...prevChat,
        messages: [...prevChat.messages, initialAssistantMessage],
        updatedAt: new Date().toISOString()
      };
    });

    try {
      setMessageLoading(true);
      setIsStreaming(true);
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      if (!token) {
        setError('Authentication required');
        handleUnauthorized();
        return;
      }

      // Create streaming handler
      const streamingHandler = new StreamingHandler({
        onProgress: (progress: ProgressUpdate) => {
          setChat(prevChat => {
            if (!prevChat) return prevChat;
            return {
              ...prevChat,
              messages: prevChat.messages.map(msg => {
                if (msg.id === assistantMessageId) {
                  const currentHistory = msg.progressHistory || [];
                  // Check if this progress phase is already in history
                  const existingIndex = currentHistory.findIndex(p => p.phase === progress.phase);
                  let newHistory;
                  
                  if (existingIndex >= 0) {
                    // Update existing progress
                    newHistory = [...currentHistory];
                    newHistory[existingIndex] = progress;
                  } else {
                    // Add new progress to history
                    newHistory = [...currentHistory, progress];
                  }
                  
                  return { 
                    ...msg, 
                    streamingProgress: progress,
                    progressHistory: newHistory
                  };
                }
                return msg;
              }),
              updatedAt: new Date().toISOString()
            };
          });
        },

        onTextChunk: (chunk: string) => {
          setChat(prevChat => {
            if (!prevChat) return prevChat;
            return {
              ...prevChat,
              messages: prevChat.messages.map(msg => {
                if (msg.id === assistantMessageId) {
                  // Add space before chunk if the last character is not a space and chunk is not punctuation
                  const lastChar = msg.content.slice(-1);
                  const needsSpace = lastChar && lastChar !== ' ' && lastChar !== '\n' && 
                                   !chunk.match(/^[.,!?;:]$/);
                  const newContent = msg.content + (needsSpace ? ' ' : '') + chunk;
                  return { ...msg, content: newContent };
                }
                return msg;
              }),
              updatedAt: new Date().toISOString()
            };
          });
        },

        onSuggestions: (suggestions: string[]) => {
          setChat(prevChat => {
            if (!prevChat) return prevChat;
            return {
              ...prevChat,
              messages: prevChat.messages.map(msg => 
                msg.id === assistantMessageId 
                  ? { ...msg, suggestions }
                  : msg
              ),
              updatedAt: new Date().toISOString()
            };
          });
        },

        onHotelResults: (hotelSearch) => {
          console.log("On hotel results: ", hotelSearch)
          setChat(prevChat => {
            if (!prevChat) return prevChat;
            return {
              ...prevChat,
              messages: prevChat.messages.map(msg => 
                msg.id === assistantMessageId 
                  ? { 
                      ...msg, 
                      pendingHotelResultsTitle: hotelSearch.resultsTitle,
                      pendingHotelResults: hotelSearch.results,
                    }
                  : msg
              ),
              updatedAt: new Date().toISOString()
            };
          });
        },

        onWebResults: (webSearch) => {
          setChat(prevChat => {
            if (!prevChat) return prevChat;
            return {
              ...prevChat,
              messages: prevChat.messages.map(msg => 
                msg.id === assistantMessageId 
                  ? { 
                      ...msg, 
                      webSearch: webSearch,
                    }
                  : msg
              ),
              updatedAt: new Date().toISOString()
            };
          });
        },

        onComplete: (finalMessage: string, metadata?: any) => {
          setIsStreaming(false);
          streamingHandlerRef.current = null;
          
          setChat(prevChat => {
            if (!prevChat) return prevChat;
            return {
              ...prevChat,
              messages: prevChat.messages.map(msg => 
                msg.id === assistantMessageId 
                  ? { 
                      ...msg, 
                      isStreaming: false,
                      finalMessage,
                      content: finalMessage,
                      streamingProgress: undefined,
                      // Keep progressHistory for reference
                      // Promote any pending hotel results to visible now
                      hotelResultsTitle: msg.pendingHotelResultsTitle || metadata?.hotelSearch?.resultsTitle,
                      hotelResults: msg.pendingHotelResults || metadata?.hotelSearch?.results,
                      // Add web search results if present in metadata
                      ...(metadata?.webSearch && {
                        webSearch: metadata.webSearch,
                      }),
                    }
                  : msg
              ),
              updatedAt: new Date().toISOString()
            };
          });

          // Update tab name if suggestion is provided
          console.log('Metadata received:', metadata);
          if (metadata?.tab_name_suggestion) {
            console.log('Updating tab name to:', metadata.tab_name_suggestion);
            setTabs(prev => prev.map(tab => 
              tab.tab_id === chatId 
                ? { ...tab, title: metadata.tab_name_suggestion }
                : tab
            ));
          } else {
            console.log('No tab_name_suggestion found in metadata');
            // Fallback: Generate tab name from first message if it's still "New Chat"
            setTabs(prev => prev.map(tab => {
              if (tab.tab_id === chatId && (tab.title === "New Chat" || !tab.title)) {
                // Generate a title from the user's first message
                console.log('Current chat messages:', chat?.messages);
                const firstUserMessage = chat?.messages.find(msg => msg.role === 'user');
                console.log('First user message:', firstUserMessage);
                if (firstUserMessage) {
                  const title = firstUserMessage.content.length > 30 
                    ? firstUserMessage.content.substring(0, 30) + '...'
                    : firstUserMessage.content;
                  console.log('Generated tab title:', title);
                  return { ...tab, title };
                }
              }
              return tab;
            }));
          }
        },

        onError: (error: Error) => {
          console.error('Streaming error:', error);
          setIsStreaming(false);
          streamingHandlerRef.current = null;
          
          // Update the assistant message with error
          setChat(prevChat => {
            if (!prevChat) return prevChat;
            return {
              ...prevChat,
              messages: prevChat.messages.map(msg => 
                msg.id === assistantMessageId 
                  ? { 
                      ...msg, 
                      isStreaming: false,
                      content: "Sorry, I encountered an error while processing your request. Please try again.",
                      streamingProgress: undefined,
                      // Keep progressHistory for reference
                    }
                  : msg
              ),
              updatedAt: new Date().toISOString()
            };
          });
        }
      });

      // Store the streaming handler reference
      streamingHandlerRef.current = streamingHandler;

      // Start streaming
      await streamingHandler.startStreaming(
        `${API_BASE_URL}/chat/message/stream`,
        {
          message: userInput,
          tab_id: chatId,
        },
        token
      );

    } catch (err) {
      console.error('Failed to send message:', err);
      setIsStreaming(false);
      streamingHandlerRef.current = null;
      
      // Update the assistant message with error
      setChat(prevChat => {
        if (!prevChat) return prevChat;
        return {
          ...prevChat,
          messages: prevChat.messages.map(msg => 
            msg.id === assistantMessageId 
              ? { 
                  ...msg, 
                  isStreaming: false,
                  content: "Sorry, I encountered an error while processing your request. Please try again.",
                  streamingProgress: undefined,
                  // Keep progressHistory for reference
                }
              : msg
          ),
          updatedAt: new Date().toISOString()
        };
      });
    } finally {
      setMessageLoading(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex h-screen bg-[#eee]">
        <div className="hidden md:block bg-[#eee]">
          <Sidebar
            tabs={tabs}
            onNewChat={handleNewChat}
            onDeleteChat={handleDeleteChat}
            onClearAll={handleClearAll}
            currentChatId={chatId}
          />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <img src="/assets/images/icons/staicey-loading.gif" alt="Loading" className="w-12 h-12 mx-auto" />
            <p className="text-gray-600">Loading chat...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex h-screen bg-[#eee]">
        <div className="hidden md:block bg-[#eee]">
          <Sidebar
            tabs={tabs}
            onNewChat={handleNewChat}
            onDeleteChat={handleDeleteChat}
            onClearAll={handleClearAll}
            currentChatId={chatId}
          />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-red-600 mb-4">
              <p className="text-lg font-semibold">Failed to load chat, please try again.</p>
            </div>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={() => retryLoadChat()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!chat) {
    return (
      <div className="flex h-screen bg-[#eee]">
        <div className="hidden md:block bg-[#eee]">
          <Sidebar
            tabs={tabs}
            onNewChat={handleNewChat}
            onDeleteChat={handleDeleteChat}
            onClearAll={handleClearAll}
            currentChatId={chatId}
          />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-red-500">Chat not found.</div>
        </div>
      </div>
    );
  }

  function auto_grow(element: HTMLTextAreaElement) {
    element.style.height = "5px";
    element.style.height = (element.scrollHeight) + "px";
  }

  return (
    <div className="flex h-screen bg-[#eee]">
      {/* Desktop Sidebar */}
      <div className="md:block bg-[#eee]">
        <Sidebar
          tabs={tabs}
          onNewChat={handleNewChat}
          onDeleteChat={handleDeleteChat}
          onClearAll={handleClearAll}
          currentChatId={chatId}
        />
      </div>

      {/* Mobile Sidebar */}
      <SidebarMobile
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        chats={tabs}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onClearAll={handleClearAll}
        currentChatId={chatId}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">

        {/* Messages */}
        <div className="flex-1 overflow-y-auto scrollbar-hide p-4 space-y-4 lg:px-10" style={{alignContent: "end"}}>
          {chat?.messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-8">
              No messages yet. Start the conversation!
            </div>
          ) : (
            chat?.messages.map((msg, idx) => {
              if (msg.hotelSearch) {
                msg.hotelResultsTitle = msg.hotelSearch.resultsTitle;
                msg.hotelResults = msg.hotelSearch.results;
              }
              const prev = chat.messages[idx - 1];
              const prevDate = prev ? prev.timestamp.split("T")[0] : null;
              const currDate = msg.timestamp.split("T")[0];

              const showDateSeparator = prevDate !== currDate;

              return (
                <div key={msg.id ? msg.id : `msg-${idx}`}>
                  {showDateSeparator && (
                    <DateSeparator date={msg.timestamp} />
                  )}
                  <ChatMessage message={msg} />
                  {idx === chat.messages.length - 1 && msg.role === "assistant" && msg.hotelResults && (
                    <div className="flex flex-col gap-4 mt-4 mx-auto w-[92%]">
                      {/* {msg.suggestions && msg.suggestions.length > 0 && ( */}
                      {msg.suggestions && msg.suggestions.length > 0 && (
                          <div className="flex flex-col gap-3 flex-wrap">
                            {msg.suggestions.map((suggestion, index) => (
                              <button 
                                key={index}
                                className="p-3 bg-[#252d63] text-white rounded-full w-fit text-sm hover:bg-[#1a1f4a] transition-colors duration-200"
                                onClick={() => {
                                  handleSend(suggestion);
                                }}
                              >
                                {suggestion}
                              </button>
                            ))}
                          </div>
                      )}
                    </div>
                  ) }
                </div>
              );
            })
          )}
          {/* Message Loading Indicator */}
          {messageLoading && (
            <div className="flex items-center space-x-2 p-4 bg-transparent justify-center rounded-lg">
              <img src="/assets/images/icons/staicey-loading.gif" alt="Loading" className="w-12 h-12" />
              <span
                className="relative z-10 text-transparent bg-clip-text w-fit
                [background-image:linear-gradient(90deg,rgba(0,0,0,1)_calc(50%_-_100px),rgba(255,255,255,0.8)_50%,rgba(255,255,255,0)_calc(50%_+_100px))]
                bg-[length:300%_100%]
                bg-no-repeat
                animate-[move-bg_1.5s_linear_infinite]"
              >
                {/* {isStreaming ? "Streaming..." : "Thinking..."} */}
                Thinking...
              </span>
              {/* <span className="text-gray-600">{getRandomLoadingMessage()}</span> */}
            </div>
          )}
          <div ref={messagesEndRef} />
          
        </div>

        {/* Input */}
        {/* <ChatInput onSend={handleSend} /> */}
        <div className="px-4 pt-1 pb-4 flex items-center gap-2 bg-transparent relative">
            <textarea
                ref={textareaRef}
                placeholder="Talk to Staicey..."
                className="flex-1 border rounded-xl px-4 py-2 focus:outline-none max-h-[400px] min-h-[100px]"
                onChange={(e) => setHasText(e.target.value.trim().length > 0)}
                onInput={(e) => auto_grow(e.target as HTMLTextAreaElement)}
                onKeyDown={(e) => {
                    if(e.key === "Enter" && !e.shiftKey && !isStreaming){
                        e.preventDefault();
                        handleSend();
                    }
                }}
                rows={1}
                disabled={loading}
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
        {/* <div className=" border-gray-200 p-4">
          <div className="flex items-center space-x-3">
            <input
              className="flex-1 border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={input}
              placeholder="Type your travel question..."
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-3 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div> */}
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <ChatPageContent />
  );
}
