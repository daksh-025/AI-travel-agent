// app/components/MobileDrawer.tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import SidebarItem from "./SidebarItem";
import { X, Plus, Trash2, Settings, User, LogOut, HelpCircle } from "lucide-react";
import { ChatSession, ChatTab } from "@/lib/types";
import { useUser } from "@/app/context/UserContext";
import SettingPopup from "./SettingPopup";
import Image from "next/image";
import { 
  AlertDialog, 
  AlertDialogAction, 
  AlertDialogCancel, 
  AlertDialogContent, 
  AlertDialogDescription, 
  AlertDialogFooter, 
  AlertDialogHeader, 
  AlertDialogTitle 
} from "@/components/ui/alert-dialog";
import Link from "next/link";

export default function MobileDrawer({ open, onClose, chats, onNewChat, onDeleteChat, onClearAll, currentChatId }: { open: boolean, onClose: () => void, chats: ChatTab[], onNewChat: () => void, onDeleteChat: (id: string) => void, onClearAll: () => void, currentChatId?: string }) {
  const { user, logout } = useUser();
  const router = useRouter();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [confirmClearAllOpen, setConfirmClearAllOpen] = useState(false);

  const handleSettingsClick = () => {
    setIsSettingsOpen(true);
  };

  const handleQuestionsClick = () => {
    router.push('/questions');
    onClose();
  };

  const handleLogoutClick = () => {
    setShowLogoutConfirm(true);
  };

  const handleLogoutConfirm = () => {
    logout();
    router.push('/');
    onClose();
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

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // Only close if clicking on the backdrop, not on the drawer content
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className={`fixed inset-0 bg-black bg-opacity-50 z-50 transition-opacity ${
        open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
      }`}
      onClick={handleBackdropClick}
    >
      <div
        className={`bg-white w-64 h-full transform transition-transform flex flex-col ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
        onClick={(e) => e.stopPropagation()} // Prevent backdrop click when clicking inside drawer
      >
        <div className="flex justify-between items-center mb-4 pt-4 pr-4">
          <span className=""></span>
          <button onClick={onClose}><X size={20} /></button>
        </div>
        <Link href="/">
          <div className="px-4 flex items-center justify-center mb-4">
            <Image src="/assets/images/logos/chat-logo.png" alt="staicey" width={140} height={50} priority={false} loading="lazy" />
          </div>
        </Link>

        <button
          onClick={onNewChat}
          className="mx-auto mb-4 rounded-full px-4 py-2 bg-gradient-to-br from-[#4f2f78] via-[#3e50a3] to-[#252d63] text-white w-fit flex justify-center items-center gap-2"
        >
          <Plus /> New Chat
        </button>
        <div className="flex justify-between px-4 border-b border-t border-gray-200 py-3">
            <span className="text-gray-500">Your Chats</span>
            <span className="text-blue-800 underline cursor-pointer" onClick={handleClearAll}>Clear All</span>
        </div>
        <div className="flex-1 overflow-y-auto mt-1">
          {chats.map((chat) => (
            <SidebarItem
              key={chat.tab_id}
              chat={chat}
              onDelete={() => handleDeleteChat(chat.tab_id)}
              isActive={chat.tab_id === currentChatId}
            />
          ))}
        </div>
        <div className="p-4 text-sm text-gray-500 flex flex-col items-center gap-2">
          <div className="flex gap-2 mb-2">
            <button 
              onClick={handleSettingsClick}
              className="w-9 h-9 border border-gray-200 rounded-full flex items-center justify-center hover:bg-gray-100 transition-colors"
              title="Settings"
            >
              <Settings size={18} />  
            </button>
            <button 
              onClick={handleQuestionsClick}
              className="w-9 h-9 border border-gray-200 rounded-full flex items-center justify-center hover:bg-gray-100 transition-colors"
              title="Questions"
            >
              <HelpCircle size={18} />  
              
            </button>
            <button 
              className="w-9 h-9 border border-gray-200 rounded-full flex items-center justify-center hover:bg-gray-100 transition-colors"
              title="User"
            >
              <User size={18} />  
            </button>
            <button 
              onClick={handleLogoutClick}
              className="w-9 h-9 border border-gray-200 rounded-full flex items-center justify-center hover:bg-gray-100 transition-colors"
              title="Logout"
            >
              <LogOut size={18} />  
            </button>
            
          </div>
          <div className="flex p-1 border border-gray-200 rounded-full items-center w-[80%] justify-start gap-2">
            <div className="w-10 h-[36px]  rounded-full flex items-center justify-center ml-2" style={{minWidth: '2.5rem'}}>
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
                {user?.username || "User"}
              </div>
          </div>
          
        </div>
      </div>
      
      {/* Settings Popup */}
      <SettingPopup 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
      
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
    </div>
  );
}
