'use client';

import { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Search, ArrowRight, SendIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import Image from 'next/image'
import { useRouter } from 'next/navigation';
import { useSignInUp } from '@/app/context/SignInUpContext';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function HeroSection() {
  // Add defensive programming for context
  const signInUpContext = useSignInUp();
  const openPopup = signInUpContext?.openPopup || (() => console.warn('SignInUpProvider not available'));
  const pendingSearchLoading = signInUpContext?.pendingSearchLoading || false;
  const pendingSearchQuery = signInUpContext?.pendingSearchQuery || "";

  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  
  
  const submitButtonRef = useRef<HTMLButtonElement>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!searchQuery.trim()) return;
    
    setIsLoading(true);
    
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        // If not authenticated, redirect to guest chat page with the query
        // Store the query in sessionStorage for the chat page to pick up
        sessionStorage.setItem('guest_query', searchQuery.trim());
        router.push(`/chat/guest`);
        setSearchQuery("")
        return;
      }

      // Send message to API
      const response = await fetch(`${API_BASE_URL}/chat/message`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: searchQuery.trim(),
        }),
      });

      if (response.status === 401) {
        // Unauthorized - redirect to guest chat with the query
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        sessionStorage.setItem('guest_query', searchQuery.trim());
        router.push(`/chat/guest`);
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // If successful, redirect to chat page
      const data = await response.json();
      router.push(`/chat/${data.tab_id}`);
      
    } catch (err) {
      console.error('Failed to send message:', err);
      // On error, redirect to guest chat page with the query
      sessionStorage.setItem('guest_query', searchQuery.trim());
      router.push(`/chat/guest`);
    } finally {
      setIsLoading(false);
    }
  };

  const sampleSuggestions = [
    'Cheapest 4+ star hotel in Brisbane for 2 adults next weekend',
    'Family holiday for 5 in Darling Harbour anytime in August',
    'Romantic couples getaway with fireplace in NZ in Winter',
    'Luxury beachfront hotel in Port Douglas for 2 weeks, 2 adults'
  ];

  return (
    
    // <div className="relative min-h-screen bg-gradient-to-br from-[#4f2f78] via-[#3e50a3] to-[#252d63] overflow-hidden">
    <div 
      style={{
        backgroundImage: 'linear-gradient(135deg, #4f2f78 0%, #3e50a3 55%, #252d63 100%)'
      }}
      className="relative min-h-screen overflow-hidden">
      
      <div className="absolute top-0 left-0 w-full h-full landing-bg z-0"></div>

      <main className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20" style={{zIndex: 1}}>
        <div className="flex items-center justify-center gap-0 lg:gap-8 mt-4">
          <div className="flex-shrink-0 sm:ml-8 justify-end">
            <div className="w-52 h-52 sm:w-52 sm:h-52 md:w-64 md:h-64 lg:w-80 lg:h-80 xl:w-96 xl:h-96 rounded-lg overflow-hidden relative">
              <Image
                src="/assets/images/images/staicey-avatar.png"
                alt="Staicey - Your AI Travel Agent"
                width="348"
                height="384"
                className="w-full h-full object-cover"
                priority
              />
            </div>
          </div>
          <div className="flex-1 text-left h-full hidden sm:block">
            <h1 className="max-w-[450px] font-bold text-white mb-4 leading-[1.2] block md:block font-manrope text-[35px] md:text-[45px] lg:text-[50px] 2xl:text-[55px]" >
              I'm Staicey<span className='inline md:inline'>
              , your shortcut to epic{' '}</span>
              {/* <span className="text-[#80d724] bg-clip-text"> */}
              <span className="text-[#8cd7e5] inline md:inline font-manrope w-fit">
                Travel Deals
              </span>
            </h1>
            <p className="max-w-[450px] text-gray-200 leading-relaxed hidden lg:block mb-1 md:mb-2" style={{fontSize:"21px"}}>
              You tell me what you're looking for & I'll charm the internet 
              into coughing up the <em>best deals</em>.
            </p>
          </div>
        </div>

        {/* Section : Textarea + Ask Button */}
        <div className="mb-5">
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 hover:shadow-xl transition-shadow duration-300">
            <textarea
              value={pendingSearchQuery == "" ? searchQuery : pendingSearchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tell me what kind of trip you're dreaming of..."
              className="w-full h-24 border-0 resize-none text-md sm:text-lg placeholder-gray-400 focus:outline-none leading-relaxed"
              rows={3}
              onKeyDown={(e) => {
                if(e.key === "Enter" && !e.shiftKey){
                    handleSearch(e);
                }
            }}
            ></textarea>
            <div className="flex justify-between items-center mt-6">
              <div className="flex items-center gap-2">
                <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors hover:scale-105 transform duration-200">
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                    />
                  </svg>
                </button>
              </div>
              <button
                className="bg-gradient-to-r from-[#182E84] via-[#554CA9] to-[#00B1CC] text-white p-2 sm:px-8 sm:py-3 rounded-full font-semibold hover:opacity-90 hover:scale-105 transform transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center gap-2"
                disabled={(isLoading || pendingSearchLoading) || (pendingSearchQuery == "" && searchQuery.length === 0)}
                onClick={handleSearch}
                ref={submitButtonRef}
              >
                <span className='hidden sm:block'>
                  {isLoading ? 'Sending...' : pendingSearchLoading ? 'Processing...' : 'Ask Staicey'}
                </span>
                {(isLoading || pendingSearchLoading) ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <SendIcon />
                )}
              </button>
            </div>
          </div>
        </div>
        <div className='flex flex-col gap-4'>
          <div className='flex justify-center items-center text-white text-center' style={{fontSize: 13}}>
            Need some inspo? Here’s some I prepared earlier...
          </div>
          <div className='flex justify-center gap-5 flex-wrap' style={{fontSize: 14}}>
            {sampleSuggestions.map((suggestion, index) => (
              <button 
                key={index}
                className='p-3 bg-[#252d63] text-white rounded-full w-fit'
                onClick={() => {
                  setSearchQuery(suggestion);
                  setTimeout(() => {
                    submitButtonRef.current?.click();
                  }, 100);
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}