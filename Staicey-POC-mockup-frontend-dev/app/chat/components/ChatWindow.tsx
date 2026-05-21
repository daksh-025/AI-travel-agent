// app/components/ChatWindow.tsx
import MessageBubble from "./MessageBubble";
import DateSeparator from "./DateSeparator";
import { Message } from "@/lib/types";

export default function ChatWindow({ messages }: { messages: Message[] }) {
  return (
    <div className="flex-1 flex flex-col h-screen">
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.map((msg, i) => (
          <div key={i}>
            {msg.dateSeparator && <DateSeparator date={msg.dateSeparator} />}
            <MessageBubble role={msg.role} content={msg.content} dateSeparator={msg.dateSeparator} id={msg.id} timestamp={msg.timestamp} />
          </div>
        ))}
      </div>
    </div>
  );
}
