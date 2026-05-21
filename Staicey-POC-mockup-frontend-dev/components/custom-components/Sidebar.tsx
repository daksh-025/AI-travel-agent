// app/components/Sidebar.tsx
"use client";
import { useState } from "react";
import SidebarItem from "./SidebarItem";
import { Plus, Trash2, PanelLeft, Settings, Settings2, User, LogOut, HelpCircle, ChevronRight, ChevronLeft } from "lucide-react";
import MobileDrawer from "./MobileDrawer";
import SettingPopup from "./SettingPopup";
import QuestionPopup from "./QuestionPopup";
import { ChatSession, ChatTab } from "@/lib/types";
import Image from "next/image";
import { useSidebar } from "@/app/context/SidebarContext";
import Link from "next/link";
import { useUser } from "@/app/context/UserContext";
import { useRouter } from "next/navigation";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";

export default function Sidebar({ tabs, onNewChat, onDeleteChat, onClearAll, currentChatId }: { 
  tabs: ChatTab[], 
  onNewChat: () => void, 
  onDeleteChat: (id: string) => void,
  onClearAll: () => void,
  currentChatId?: string 
}) {
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [questionOpen, setQuestionOpen] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [confirmClearAllOpen, setConfirmClearAllOpen] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  
  // Add defensive programming for contexts
  const sidebarContext = useSidebar();
  const userContext = useUser();
  
  const { collapsed, toggleCollapsed } = sidebarContext || {
    collapsed: false,
    toggleCollapsed: () => console.warn('SidebarProvider not available'),
  };
  
  const { user, isAuthenticated, logout } = userContext || {
    user: null,
    isAuthenticated: false,
    logout: () => console.warn('UserProvider not available'),
  };

  const handleDeleteChat = (id: string) => {
    setConfirmDeleteId(id);
  };

  const handleConfirmDelete = () => {
    if (confirmDeleteId) {
      onDeleteChat(confirmDeleteId);
      setConfirmDeleteId(null);
    }
  };

  const handleClearAll = () => {
    setConfirmClearAllOpen(true);
  };

  const handleConfirmClearAll = () => {
    onClearAll();
    setConfirmClearAllOpen(false);
  };

  const handleLogoutClick = () => {
    setShowLogoutConfirm(true);
  };

  const handleLogoutConfirm = () => {
    logout();
    router.push('/');
    setShowLogoutConfirm(false);
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const formatDisplayName = (name: string) => {
    if (!name) return '';
    const nameParts = name.split(' ');
    if (nameParts.length === 1) return nameParts[0];
    return `${nameParts[0]} ${nameParts[1]?.[0] || ''}.`;
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        className="lg:hidden p-2 fixed top-4 left-4 z-50 bg-gray-100 rounded-lg"
        onClick={() => setDrawerOpen(true)}
      >
        <PanelLeft size={20} />
      </button>

      {/* Desktop Sidebar */}
      <aside className={`hidden lg:flex flex-col bg-white h-screen rounded-br-[40px] rounded-tr-[40px] relative transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-64'
      }`}>
        {/* <div className="p-4 flex items-center justify-end pb-0 mr-1">
          <button 
            onClick={toggleCollapsed}
            className="text-gray-500 cursor-pointer hover:text-gray-700"
          >
            <PanelLeft size={20} />
          </button>
        </div> */}
        
        {!collapsed ? (
          <Link href="/">
            <div className="px-4 flex items-center justify-center mb-4 mt-7">
              {/* <Image src="/assets/images/logos/Staicey-logo-chat-window.png" alt="staicey" width={140} height={50} loading="lazy" /> */}
              <Image src="/assets/images/logos/chat-logo.png" alt="staicey" width={140} height={50} loading="lazy" />
            </div>
          </Link>
          ) : (
            <Link href="/">
              <div className="px-4 flex items-center justify-center mb-4 mt-7">
                <Image src="/assets/images/logos/only-logo-chat.png" alt="staicey" width={140} height={50} />
              </div>
            </Link>
            )
        }

        {!collapsed ? (
          <button
            onClick={onNewChat}
            className="mx-auto mb-4 rounded-full px-6 py-2 bg-gradient-to-br from-[#4f2f78] via-[#3e50a3] to-[#252d63] text-white w-fit flex justify-center items-center gap-2"
          >
            <Plus /> New Chat
          </button>
        ) : (
          <button
            onClick={onNewChat}
            className="mx-auto mb-4 rounded-full p-2 bg-gradient-to-br from-[#4f2f78] via-[#3e50a3] to-[#252d63] text-white"
            title="New Chat"
          >
            <Plus size={20} />
          </button>
        )}

        {!collapsed && (
          <div className="flex justify-between px-4 border-b border-t border-gray-200 py-3">
            <span className="text-gray-500">Your Chats</span>
            <span className="text-blue-800 underline cursor-pointer" onClick={handleClearAll}>Clear All</span>
          </div>
        )}

        <div className="flex-1 overflow-y-auto mt-1">
          {tabs
            .filter((chat) => chat && chat.tab_id) // Filter out invalid chat objects
            .map((chat) => (
              <SidebarItem
                key={chat.tab_id}
                chat={chat}
                onDelete={() => handleDeleteChat(chat.tab_id)}
                isActive={chat.tab_id === currentChatId}
                collapsed={collapsed}
              />
            ))}
        </div>

        <div className="p-4 text-sm text-gray-500 cursor-pointer flex flex-col items-center gap-2">
          <div className={`flex gap-2 mb-2 ${collapsed ? 'flex-col' : 'flex-row'}`}>
            <div className="w-9 h-9 border border-gray-200 rounded-full flex items-center justify-center cursor-pointer hover:bg-gray-100" onClick={() => setSettingsOpen(true)}>
              <Settings size={18} />  
            </div>
            <div className="w-9 h-9 border border-gray-200 rounded-full flex items-center justify-center hover:bg-gray-100" onClick={() => setQuestionOpen(true)}>
              <HelpCircle size={18}  />  
            </div>
            <div className="w-9 h-9 border border-gray-200 rounded-full flex items-center justify-center">
              <User size={18}  />  
            </div>
            <div className="w-9 h-9 border border-gray-200 rounded-full flex items-center justify-center cursor-pointer hover:bg-gray-100" onClick={handleLogoutClick}>
              <LogOut size={18} />  
            </div>
          </div>
          
          {!collapsed ? (
            <div className="flex gap-2 p-2 border border-gray-200 rounded-full items-center w-[80%] justify-start">
              <div className="w-10 h-[36px]  rounded-full flex items-center justify-center" style={{minWidth: '2.5rem'}}>
                {/* {getInitials(user?.username || '')} */}
                <Image
                  src={user?.avatarUrl ? user.avatarUrl : '/assets/images/icons/user-icon.png'}
                  alt="User Avatar"
                  className="w-[42px] h-[36px] rounded-full"
                  width="42"
                  height="36"
                />
              </div>
              <div className="capitalize line-clamp-1">
                {formatDisplayName(user?.username || '')}
              </div>
            </div>
          ) :(
            <div className="flex gap-1 rounded-full items-center justify-start">
              <div className="w-10 h-10  rounded-full flex items-center justify-center">
                {/* {getInitials(user?.username || '')} */}
                <Image
                  src={user?.avatarUrl ? user.avatarUrl : '/assets/images/icons/user-icon.png'}
                  alt="User Avatar"
                  className="w-[42px] h-[36px] rounded-full"
                  width="42"
                  height="36"
                />
              </div>
            </div>
          )

        }
        </div>

        <div className="absolute bottom-[50%] -right-3 w-3 h-10 bg-white flex rounded-br-full rounded-tr-full cursor-pointer" onClick={() => toggleCollapsed()}>
          <span className="h-fit my-auto text-xs text-gray-600">
            {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
          </span>
        </div>
      </aside>

      {/* Mobile Drawer */}
      <MobileDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        chats={tabs}
        onNewChat={onNewChat}
        onDeleteChat={onDeleteChat}
        onClearAll={onClearAll}
        currentChatId={currentChatId}
      />

      {/* Settings Popup */}
      <SettingPopup
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />

      {/* Question Popup */}
      <QuestionPopup
        isOpen={questionOpen}
        onClose={() => setQuestionOpen(false)}
      />

      {/* Confirm Delete Single Chat */}
      <AlertDialog open={!!confirmDeleteId} onOpenChange={(open) => !open && setConfirmDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete chat?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. The chat and its messages will be permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Confirm Clear All Chats */}
      <AlertDialog open={confirmClearAllOpen} onOpenChange={setConfirmClearAllOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Clear all chats?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove all chats. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmClearAll}>Clear All</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Logout Confirmation Dialog */}
      {showLogoutConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-lg p-6 max-w-sm mx-4">
            <h3 className="text-lg font-semibold mb-4">Confirm Logout</h3>
            <p className="text-gray-600 mb-6">Are you sure you want to logout?</p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowLogoutConfirm(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleLogoutConfirm}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
