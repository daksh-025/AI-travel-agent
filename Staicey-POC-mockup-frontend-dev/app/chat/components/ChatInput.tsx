// app/components/ChatInput.tsx
"use client";
import { useState } from "react";
import { Send } from "lucide-react";

export default function ChatInput({ onSend }: { onSend: (text: string) => void }) {
  const [text, setText] = useState("");

  function auto_grow(element: HTMLTextAreaElement) {
    element.style.height = "5px";
    element.style.height = (element.scrollHeight) + "px";
  }

  return (
    <div className="p-4 flex items-center gap-2 bg-transparent relative">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Talk to Staicey..."
        className="flex-1 border rounded-xl px-4 py-2 focus:outline-none max-h-[400px] min-h-[100px]"
        onInput={(e) => auto_grow(e.target as HTMLTextAreaElement)}
        rows={1}
      />
      <button
        onClick={() => { onSend(text); setText(""); }}
        className="bg-purple-600 text-white p-2 rounded-full absolute bottom-7 right-10"
      >
        <Send size={18} />
      </button>
    </div>
  );
}
