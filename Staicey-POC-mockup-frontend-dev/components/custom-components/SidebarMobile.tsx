// app/components/MobileDrawer.tsx
"use client";
import { ChatTab } from "@/lib/types";
import SidebarItem from "./SidebarItem";
import { X, Plus, Trash2 } from "lucide-react";

export default function MobileDrawer({ open, onClose, chats, onNewChat, onDeleteChat, onClearAll, currentChatId }: { 
  open: boolean, 
  onClose: () => void, 
  chats: ChatTab[], 
  onNewChat: () => void, 
  onDeleteChat: (id: string) => void,
  onClearAll: () => void,
  currentChatId?: string 
}) {
  return (
    <div
      className={`fixed inset-0 bg-black bg-opacity-50 z-50 transition-opacity ${
        open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
      }`}
    >
      <div
        className={`bg-white w-64 h-full transform transition-transform ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex justify-between items-center mb-4">
          <span className="font-bold text-xl"></span>
          <button onClick={onClose}><X size={20} /></button>
        </div>
        <button
          onClick={() => { onNewChat(); onClose(); }}
          className="mb-4 px-4 py-2 bg-purple-600 text-white rounded-lg flex items-center gap-2"
        >
          <Plus /> New Chat
        </button>
        <div className="flex-1 overflow-y-auto">
          {chats
            .filter((chat) => chat && chat.tab_id) // Filter out invalid chat objects
            .map((chat) => (
              <SidebarItem
                key={chat.tab_id}
                chat={chat}
                onDelete={() => onDeleteChat(chat.tab_id)}
                isActive={chat.tab_id === currentChatId}
              />
            ))}
        </div>
        <div className="mt-4 text-sm text-gray-500 cursor-pointer flex items-center gap-2" onClick={onClearAll}>
          <Trash2 /> Clear All
        </div>
      </div>
    </div>
  );
}
