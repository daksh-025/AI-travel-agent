"use client";

import { ChatTab } from "@/lib/types";
import { useEffect, useRef } from "react";
import { Trash2 } from "lucide-react";
import Link from "next/link";
import { createSafeChatHref } from "@/lib/utils/linkValidation";

type Props = {
  chat: ChatTab;
  onDelete?: () => void;
  isActive?: boolean;
  collapsed?: boolean;
};

function formatDate(dateStr: string) {
  if (!dateStr) return "";

  // Normalize incoming date string. If there's no timezone info, treat it as UTC (append 'Z').
  // This avoids interpreting UTC timestamps as local time by default.
  let normalized = dateStr.trim();

  // Replace space between date and time with 'T' if present
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(normalized)) {
    normalized = normalized.replace(" ", "T");
  }

  // If no explicit timezone (no 'Z' and no +HH:MM/-HH:MM), default to UTC
  const hasTimezone = /Z$|[+-]\d{2}:\d{2}$/.test(normalized);
  if (!hasTimezone) {
    // If it's date-only, add midnight UTC
    if (/^\d{4}-\d{2}-\d{2}$/.test(normalized)) {
      normalized = `${normalized}T00:00:00Z`;
    } else {
      normalized = `${normalized}Z`;
    }
  }

  const d = new Date(normalized);

  if (isNaN(d.getTime())) {
    return "";
  }

  return d
    .toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })
    .toUpperCase();
}

export default function SidebarItem({ chat, onDelete, isActive = false, collapsed = false }: Props) {
  // Add defensive check for chat
  if (!chat) {
    console.warn('SidebarItem: Invalid chat object', chat);
    return null;
  }

  const chatHref = createSafeChatHref(chat.tab_id);

  // Ensure the active item is visible in the scroll container
  const itemRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (isActive && itemRef.current) {
      try {
        itemRef.current.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      } catch {}
    }
  }, [isActive]);

  if (collapsed) {
    return (
      <Link href={chatHref}>
        <div
            ref={itemRef}
            // onClick={handleNavigate}
            className={`flex items-center justify-center p-2 m-1 cursor-pointer transition-colors rounded-lg ${
            isActive ? "bg-gray-100" : "hover:bg-gray-50"
            }`}
            title={chat.title || "Untitled Chat"}
        >
            <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-xs font-medium">
            {(chat.title || "C").charAt(0).toUpperCase()}
            </div>
        </div>
      </Link>
    );
  }

  return (
    <Link href={chatHref}>
        <div
        ref={itemRef}
        // onClick={handleNavigate}
        className={`flex items-center justify-between p-3 mx-1 rounded-lg cursor-pointer transition-colors border-l-2 ${
            isActive 
              ? "bg-gray-50 border-[#252d63]" 
              : "hover:bg-gray-50 border-transparent"
        }`}
        >
        <div className="min-w-0">
            <div className={`text-sm line-clamp-2 ${isActive ? 'font-semibold text-[#252d63]' : 'font-medium'}`}>{chat.title || "Untitled Chat"}</div>
            <div className="text-xs text-gray-400 mt-1">{formatDate(chat.last_activity || "")}</div>
        </div>

        <button
            onClick={(e) => {
                e.preventDefault();
                onDelete?.();
            }}
            aria-label="Delete chat"
            className="ml-3 text-gray-400 hover:text-red-500 p-1 rounded-full focus:outline-none focus:ring-0"
        >
            <Trash2 size={16} />
        </button>
        </div>
    </Link>
  );
}
