import { Message } from "@/lib/types";

export default function MessageBubble({ role, content }: Message) {
  const isUser = role === "user";
  return (
    <div className={`flex items-end gap-2 ${isUser ? "flex-row-reverse" : ""}`}>
      <img
        src={isUser ? "/user-avatar.jpg" : "/bot-avatar.jpg"}
        alt={role}
        className="w-8 h-8 rounded-full"
      />
      <div
        className={`px-4 py-2 rounded-2xl max-w-lg ${
          isUser
            ? "bg-purple-700 text-white rounded-br-none"
            : "bg-white text-gray-900 rounded-bl-none"
        }`}
      >
        {content}
      </div>
    </div>
  );
}
