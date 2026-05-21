// components/custom-components/RateLimitBanner.tsx
"use client";

import { Info, Clock } from 'lucide-react';
import { RateLimitInfo } from '@/hooks/useRateLimit';
import { RATE_LIMIT_CONFIG } from '@/lib/constants/rateLimit';

interface RateLimitBannerProps {
  rateLimitInfo: RateLimitInfo | null;
  resetTimeFormatted: string;
  onSignUpClick: () => void;
}

export default function RateLimitBanner({ 
  rateLimitInfo, 
  resetTimeFormatted,
  onSignUpClick 
}: RateLimitBannerProps) {
  // Don't show banner for authenticated users
  if (!rateLimitInfo || rateLimitInfo.type === 'authenticated') {
    return null;
  }

  const remaining = rateLimitInfo.remaining as number;
  const limit = rateLimitInfo.limit || RATE_LIMIT_CONFIG.guestDailyLimit;
  const usage = rateLimitInfo.usage || 0;

  // Determine banner color based on remaining requests
  const getBannerColor = () => {
    if (remaining === 0) return 'bg-red-50 border-red-200 text-red-800';
    if (remaining === 1) return 'bg-orange-50 border-orange-200 text-orange-800';
    return 'bg-blue-50 border-blue-200 text-blue-800';
  };

  const getIconColor = () => {
    if (remaining === 0) return 'text-red-500';
    if (remaining === 1) return 'text-orange-500';
    return 'text-blue-500';
  };

  return (
    <div className={`${getBannerColor()} border-b px-4 py-3`}>
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <Info className={`w-5 h-5 ${getIconColor()} flex-shrink-0`} />
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium">
              {remaining === 0 ? (
                RATE_LIMIT_CONFIG.messages.dailyLimitReached
              ) : (
                RATE_LIMIT_CONFIG.messages.freeSearchesRemaining(remaining, limit)
              )}
            </span>
            {resetTimeFormatted && remaining === 0 && (
              <span className="flex items-center gap-1 text-sm opacity-90">
                <Clock className="w-4 h-4" />
                Resets in {resetTimeFormatted}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={onSignUpClick}
          className="px-4 py-1.5 bg-[#7C3AED] text-white rounded-lg font-medium hover:opacity-90 transition-opacity text-sm whitespace-nowrap"
        >
          {RATE_LIMIT_CONFIG.messages.signUpPrompt}
        </button>
      </div>
    </div>
  );
}

