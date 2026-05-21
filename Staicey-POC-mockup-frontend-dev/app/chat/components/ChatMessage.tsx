// components/ChatMessage.tsx
"use client";

import { FC, useState } from "react";
import { Message } from "@/lib/types";
import clsx from "clsx";
import { UserCircle, Sparkles, X } from "lucide-react";
import Image from "next/image";
import HotelResults from "./HotelResults";
import StreamingProgress from "./StreamingProgress";

type ChatMessageProps = {
  message: Message;
};

// Function to convert markdown to HTML
const convertMarkdownToHtml = (text: string): string => {
  if (!text) return text;
  
  let html = text;
  
  // Convert line breaks to <br> tags
  html = html.replace(/\n/g, '<br>');
  
  // Convert numbered lists (1. item, 2. item, etc.) - handle multi-line items
  html = html.replace(/^(\d+\.\s+.*?)(?=\n\d+\.|\n\n|$)/gm, '<div class="ml-4 mb-2"><strong>$1</strong></div>');
  
  // Convert bullet points (- item, * item) - handle multi-line items
  html = html.replace(/^[\-\*]\s+(.*?)(?=\n[\-\*]|\n\n|$)/gm, '<div class="ml-4 mb-1">• $1</div>');
  
  // Convert sub-bullet points (  - item,   * item)
  html = html.replace(/^  [\-\*]\s+(.*?)(?=\n  [\-\*]|\n\n|$)/gm, '<div class="ml-8 mb-1">◦ $1</div>');
  
  // Convert bold markdown (**text** or __text__) to HTML
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Convert italic markdown (*text* or _text_) to HTML
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/_(.*?)_/g, '<em>$1</em>');
  
  // Convert href markdown ([text](url)) to HTML
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">$1</a>');
  
  // AU spelling: apologize -> apologise
  html = html.replace(/apologize/g, 'apologise');
  
  // Convert domain strings to clickable links
  // html = html.replace(/\b(?:www\.)?([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.(?:com|com\.au|org|net|edu|gov|mil|biz|info|io|co|uk|au))\b/g, '<a href="https:////$&" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">$&</a>');
  
  return html;
};

const ChatMessage: FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";
  const [selectedImage, setSelectedImage] = useState<{url: string, description: string} | null>(null);
  
  // Use finalMessage if available (for completed streaming), otherwise use content
  const displayContent = message.finalMessage || message.content;

  return (
    <>
      {/* Streaming Progress List - Full Width */}
      {isAssistant && message.streamingProgress && message.streamingProgress.percentage !== 100 && (
        <div className="w-full mb-2 ml-[60px]">
          <div className="flex flex-col gap-2">
            <StreamingProgress 
              progress={message.streamingProgress} 
              isVisible={true}
            />
          </div>
        </div>
      )}
      
      {/* Web Search Images */}
      {message.webSearch && message.webSearch.images && message.webSearch.images.length > 0 && (
        <div className="flex flex-col w-[92%] mx-auto mb-4 pr-12">
          {message.webSearch.resultsTitle && (
            <div className="text-gray-900 text-sm font-bold mb-4">
              {message.webSearch.resultsTitle}
            </div>
          )}
           <div className="flex flex-wrap gap-4">
               {message.webSearch.images.slice(0, 4).map((image :any, index : number) => (
                 <div key={index} className="bg-white rounded-lg overflow-hidden shadow-md w-full sm:w-[calc(50%-0.5rem)] 2xl:w-[calc(25%-0.75rem)] cursor-pointer hover:shadow-lg transition-shadow duration-200" onClick={() => setSelectedImage(image)}>
                  <img
                    src={image.url}
                    alt={image.description || `Search result image ${index + 1}`}
                    className="w-full h-48 object-cover"
                    loading="lazy"
                    onError={(e) => {
                      e.currentTarget.parentElement!.style.display = 'none';
                    }}
                  />
                  {image.description && (
                    <div className="p-3 text-xs text-gray-600">
                      {image.description}
                    </div>
                  )}
                </div>
              ))}
          </div>
        </div>
      )}
      
      <div
        className={clsx(
          "flex gap-3 w-full",
          isUser ? "justify-end" : "justify-start"
        )}
      >
        {/* Avatar */}
        {!isUser && (
          <div className="flex-shrink-0">
            {isAssistant ? (
              <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center text-white">
                {/* <Sparkles className="w-6 h-6" /> */}
                <Image
                  src="/assets/images/images/staicey-avatar.png"
                  alt="Staicey"
                  width="20"
                  height="20"
                  style={{ height: 'auto', width: '100%', borderRadius: 40 }}
                  priority
                />
              </div>
            ) : (
              <div className="w-10 h-10 rounded-full bg-gray-300" />
            )}
          </div>
        )}
        {/* Message bubble */}
        {
          message.content && (
            <div
          className={clsx(
            "max-w-[75%] rounded-xl px-4 py-4 text-sm whitespace-pre-wrap break-words",
            isUser
              ? "bg-[#4f2f78] text-white "
              : "bg-white text-gray-900 "
          )}
          dangerouslySetInnerHTML={{ __html: convertMarkdownToHtml(message.content) }}
        />
          )
        }
        
        {/* <div
          className={clsx(
            "max-w-[75%] rounded-xl px-4 py-4 text-sm whitespace-pre-wrap break-words",
            isUser
              ? "bg-[#4f2f78] text-white "
              : "bg-white text-gray-900 "
          )}
        >
          {message.content} 
        </div> */}

        {/* User Avatar */}
        {isUser && (
          <div className="flex-shrink-0">
            <img
              src={message.avatarUrl ? message.avatarUrl : '/assets/images/icons/user-icon.png'}
              alt="User Avatar"
              className="w-[48px] h-[40px] rounded-full object-cover"
            />
          </div>
        )}
      </div>
      {message.hotelResults && message.hotelResults.length > 0 && message.hotelResultsTitle && (
        <div className="w-[92%] mx-auto text-gray-900 text-sm md:text-lg font-bold mt-2 md:mt-4">
          {message.hotelResultsTitle}
        </div>
      )}
      {message.hotelResults && (
        <div className="flex flex-col gap-4 mt-2 mx-auto w-[92%]">
          <HotelResults
            hotels={message.hotelResults}
            // mapEmbedUrl="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d35384.69539349266!2d153.374133!3d-28.016666!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x6b911a24614c7417%3A0x502a35af3deaf50!2sGold%20Coast%20QLD%2C%20Australia!5e0!3m2!1sen!2sau!4v1691553385423!5m2!1sen!2sau"
            mapEmbedUrl={`https://www.google.com/maps/embed/v1/search?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&q=hotels+in+Gold+Coast+Australia`}
          />
        </div>
      )}
      
      {/* {message.hotelResults} */}
      
      {/* Full-screen Image Modal */}
      {selectedImage && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4 flex-col"
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-4xl max-h-full">
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-4 right-4 text-white hover:text-gray-300 z-10 bg-black bg-opacity-50 rounded-full p-2"
            >
              <X className="w-6 h-6" />
            </button>
            <img
              src={selectedImage.url}
              alt={selectedImage.description || "Full screen image"}
              className="max-w-full max-h-full object-contain rounded-md"
            />
          </div>
          {selectedImage.description && (
            <div className="mt-4 bg-black bg-opacity-75 text-white text-center p-4 rounded-lg">
              <p className="text-sm">{selectedImage.description}</p>
            </div>
          )}
        </div>
      )}
    </>

  );
};

export default ChatMessage;
