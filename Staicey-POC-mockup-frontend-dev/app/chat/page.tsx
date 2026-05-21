"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ChatSession, ChatTab } from "@/lib/types";
import Sidebar from "@/components/custom-components/Sidebar";
import SidebarMobile from "@/components/custom-components/SidebarMobile";
import SettingPopup from "@/components/custom-components/SettingPopup";
import { Plus, MessageSquare, Loader2 } from "lucide-react";
import { useUser } from "@/app/context/UserContext";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
// interface ChatTab {
//   tab_id: string;
//   title: string;
//   session_id: string;
//   created_at: string;
//   last_activity: string;
//   message_count: number;
//   is_active: boolean;
//   is_pinned: boolean;
//   order_index: number;
// }

export default function ChatPage() {
  const router = useRouter();
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [tabs, setTabs] = useState<ChatTab[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showOnboardingPopup, setShowOnboardingPopup] = useState(false);
  const [checkingPreferences, setCheckingPreferences] = useState(true);
  const [hasDismissedPopup, setHasDismissedPopup] = useState(false);
  const [settingPopupOpen, setSettingPopupOpen] = useState(false);
  const { user, logout } = useUser();

  // Reusable function to handle 401 errors
  const handleUnauthorized = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    logout();
    router.push('/');
    // window.location.reload();
  };

  // Reset dismissed state when user completes quiz
  const resetDismissedState = () => {
    setHasDismissedPopup(false);
  };

  // Check if user has travel preferences
  const checkTravelPreferences = (forceCheck = false) => {
    try {
      if (!user) {
        setCheckingPreferences(false);
        return;
      }

      // Check if user has searchPreferences and if it's not empty
      const hasPreferences = user.preferences?.searchPreferences && user.preferences.searchPreferences.length > 0;

      if (!hasPreferences) {
        // User has no search preferences, show onboarding popup
        if (!hasDismissedPopup && !settingPopupOpen) {
          setShowOnboardingPopup(true);
        }
      } else {
        // User has preferences, hide popup if it was showing
        setShowOnboardingPopup(false);
        setHasDismissedPopup(false); // Reset dismissed state when preferences exist
      }
    } catch (error) {
      console.error('Error checking travel preferences:', error);
      // On error, assume no preferences and show popup only if not dismissed
      if (!hasDismissedPopup && !settingPopupOpen) {
        setShowOnboardingPopup(true);
      }
    } finally {
      setCheckingPreferences(false);
    }
  };

  // Fetch chat tabs from API
  const fetchChatTabs = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      if (!token) {
        setError('Authentication required');
        setLoading(false);
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

      // Convert tabs to ChatSession format for compatibility
      const convertedChats: ChatSession[] = validTabs.map(tab => ({
        id: tab.tab_id,
        title: tab.title || 'Untitled Chat',
        createdAt: tab.created_at || new Date().toISOString(),
        updatedAt: tab.last_activity || new Date().toISOString(),
        messages: [], // We'll fetch messages separately if needed
      }));

      setChats(convertedChats);
    } catch (err) {
      console.error('Failed to fetch chat tabs:', err);
      setError(err instanceof Error ? err.message : 'Failed to load chats');
      handleUnauthorized();
    } finally {
      setLoading(false);
    }
  };

  // Fetch tabs immediately on component mount
  useEffect(() => {
    fetchChatTabs();
  }, []);

  // Check preferences when user data changes
  useEffect(() => {
    if (user) {
      checkTravelPreferences();
    }
  }, [user]);

  // Note: Removed automatic preference checking to prevent popup from reappearing
  // Preferences are only checked on initial page load

  // Note: Removed focus event listener to prevent popup from reappearing
  // Preferences will be checked on page load and when user explicitly navigates

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
      const newChat: ChatSession = {
        id: newTab.tab_id,
        title: newTab.title,
        createdAt: newTab.created_at,
        updatedAt: newTab.last_activity,
        messages: [],
      };
      
      setChats(prev => [newChat, ...prev]);
      
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
      setChats(prev => prev.filter(chat => chat.id !== chatId));
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

      // Clear all chats from state
      setTabs([]);
      setChats([]);
    } catch (err) {
      console.error('Failed to clear all chats:', err);
      setError(err instanceof Error ? err.message : 'Failed to clear all chats');
    }
  };

  const handleChatSelect = (chatId: string) => {
    router.push(`/chat/${chatId}`);
  };

  // Loading state - only wait for chat tabs, not preferences
  if (loading) {
    return (
      <div className="flex h-screen bg-gray-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <img src="/assets/images/icons/staicey-loading.gif" alt="Loading" className="w-12 h-12 mx-auto" />
            <p className="text-gray-600">Loading your chats...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    handleUnauthorized();   
    return;
    return (
      <div className="flex h-screen bg-gray-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-red-600 mb-4">
              <MessageSquare className="w-12 h-12 mx-auto mb-2" />
              <p className="text-lg font-semibold">Failed to load chats</p>
            </div>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={fetchChatTabs}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Onboarding Popup - show as overlay on top of chat page
  const onboardingPopup = showOnboardingPopup && (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-2xl w-full p-8 text-center shadow-2xl">
        <div className="mb-6">
          <div 
            className="mx-auto w-20 h-20 rounded-full flex items-center justify-center mb-4"
            style={{
              backgroundImage: 'linear-gradient(135deg, #4f2f78 0%, #3e50a3 55%, #252d63 100%)'
            }}
          >
            <MessageSquare className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Let's identify your travel "Preferences"
          </h2>
          <p className="text-lg text-gray-600 leading-relaxed">
            So I can get to know you a little better and give you the best personalised recommendations,
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => {
              resetDismissedState();
              setShowOnboardingPopup(false);
              setSettingPopupOpen(true);
            }}
            style={{
              backgroundImage: 'linear-gradient(135deg, #4f2f78 0%, #3e50a3 55%, #252d63 100%)'
            }}
            className="px-8 py-4 text-white font-semibold rounded-full hover:shadow-lg transition-all duration-200 text-lg"
          >
            Set Travel Preferences
          </button>
          <button
            onClick={() => {
              setShowOnboardingPopup(false);
              setHasDismissedPopup(true);
            }}
            className="px-8 py-4 text-gray-600 font-semibold rounded-full border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-50 transition-all duration-200 text-lg"
          >
            Maybe Later
          </button>
        </div>
        
        <p className="text-sm text-gray-500 mt-6">
          This will only take one minute and will help me provide much better recommendations!
        </p>
      </div>
    </div>
  );

  return (
    <>
      <div className="flex h-screen bg-gray-50">
        {/* Desktop Sidebar */}
        <div className="block bg-[#eee] ">
          <Sidebar
            tabs={tabs}
            onNewChat={handleNewChat}
            onDeleteChat={handleDeleteChat}
            onClearAll={handleClearAll}
            currentChatId={undefined}
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
          currentChatId={undefined}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Welcome Content */}
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-[#eee]">
            <div className="max-w-md">
              {/* <div 
              className="mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-6"
                style={{
                  backgroundImage: 'linear-gradient(135deg, #4f2f78 0%, #3e50a3 55%, #252d63 100%)'
                }}
              >
                <MessageSquare className="w-8 h-8 text-white" />
              </div> */}
              <div className="text-center text-gray-500 mt-8">
                <img 
                  src="/assets/images/images/staicey-avatar.png" 
                  alt="Staicey" 
                  className="w-32 h-32 md:w-44 md:h-44 lg:w-52 lg:h-52 mx-auto mb-4"
                />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Welcome, I'm Staicey
              </h2>
              <p className="text-gray-600 mb-8">
                I'm here to help you plan amazing trips, discover new destinations, and create unforgettable travel experiences.
              </p>
              <button
                onClick={handleNewChat}
                style={{
                  backgroundImage: 'linear-gradient(135deg, #4f2f78 0%, #3e50a3 55%, #252d63 100%)'
                }}
                className="inline-flex items-center px-6 py-3 text-white font-medium rounded-full hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                <Plus className="w-5 h-5 mr-2" />
                Start New Chat
              </button>
              
              {/* Check Preferences Button - only show if user dismissed popup */}
              {hasDismissedPopup && (
                <button
                  onClick={() => {
                    setHasDismissedPopup(false);
                    setSettingPopupOpen(true);
                  }}
                  className="block mt-4 text-blue-600 hover:text-blue-700 text-sm mx-auto"
                >
                  Set travel preferences for better recommendations
                </button>
              )}
              
              {/* Background preference checking indicator */}
              {checkingPreferences && (
                <div className="mt-4 text-xs text-gray-500 flex items-center justify-center">
                  <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                  Checking preferences...
                </div>
              )}
            </div>

            {/* Recent Chats Preview */}
            {false && chats.length > 0 && (
              <div className="mt-12 w-full max-w-2xl">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Chats</h3>
                <div className="grid gap-3">
                  {chats.slice(0, 3).map((chat) => (
                    <div
                      key={chat.id}
                      onClick={() => handleChatSelect(chat.id)}
                      className="bg-white p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200 cursor-pointer"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {chat.title}
                          </h4>
                          <p className="text-xs text-gray-500 mt-1">
                            {chat.updatedAt ? new Date(chat.updatedAt).toLocaleDateString() : 'Unknown date'}
                          </p>
                        </div>
                        <div className="ml-4 text-xs text-gray-400">
                          {chat.messages.length} messages
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Onboarding Popup Overlay */}
      {onboardingPopup}
      
      {/* Setting Popup */}
      <SettingPopup
        isOpen={settingPopupOpen}
        onClose={() => setSettingPopupOpen(false)}
        initialTab="preferences"
      />
    </>
  );
} 