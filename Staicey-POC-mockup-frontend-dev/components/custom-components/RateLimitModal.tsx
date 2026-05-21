// components/custom-components/RateLimitModal.tsx
"use client";

import { Clock, Lock, Zap, Check } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { RATE_LIMIT_CONFIG } from '@/lib/constants/rateLimit';

interface RateLimitModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSignUp: () => void;
  resetTimeFormatted: string;
}

export default function RateLimitModal({ 
  isOpen, 
  onClose, 
  onSignUp,
  resetTimeFormatted 
}: RateLimitModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px] bg-white">
        <DialogHeader>
          <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-r from-purple-100 to-pink-100">
            <Lock className="w-8 h-8 text-purple-600" />
          </div>
          <DialogTitle className="text-2xl font-bold text-center">
            {RATE_LIMIT_CONFIG.messages.dailyLimitReached}
          </DialogTitle>
          <DialogDescription className="text-center text-gray-600 pt-2">
            {RATE_LIMIT_CONFIG.messages.limitExceededMessage(RATE_LIMIT_CONFIG.guestDailyLimit)}
            {resetTimeFormatted && (
              <span className="flex items-center justify-center gap-2 mt-2 text-sm">
                <Clock className="w-4 h-4" />
                Resets in {resetTimeFormatted}
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Benefits */}
          <div className="space-y-3">
            <p className="text-sm font-semibold text-gray-900">
              Sign up for unlimited access and get:
            </p>
            <ul className="space-y-2">
              <li className="flex items-start gap-3">
                <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center mt-0.5">
                  <Check className="w-3 h-3 text-green-600" />
                </div>
                <span className="text-sm text-gray-700">
                  <strong>Unlimited searches</strong> - No daily limits
                </span>
              </li>
              <li className="flex items-start gap-3">
                <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center mt-0.5">
                  <Check className="w-3 h-3 text-green-600" />
                </div>
                <span className="text-sm text-gray-700">
                  <strong>Save your chats</strong> - Access your search history anytime
                </span>
              </li>
              <li className="flex items-start gap-3">
                <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center mt-0.5">
                  <Check className="w-3 h-3 text-green-600" />
                </div>
                <span className="text-sm text-gray-700">
                  <strong>Personalized recommendations</strong> - Based on your preferences
                </span>
              </li>
              <li className="flex items-start gap-3">
                <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center mt-0.5">
                  <Zap className="w-3 h-3 text-yellow-600" />
                </div>
                <span className="text-sm text-gray-700">
                  <strong>Priority support</strong> - Get help when you need it
                </span>
              </li>
            </ul>
          </div>

          {/* CTA Buttons */}
          <div className="space-y-3 pt-2">
            <button
              onClick={onSignUp}
              className="w-full px-6 py-3 bg-gradient-to-r from-[#7C3AED] to-[#401191] text-white rounded-lg font-semibold hover:opacity-90 transition-opacity shadow-lg"
            >
              Sign Up Now - It's Free!
            </button>
            <button
              onClick={onClose}
              className="w-full px-6 py-2 text-gray-600 hover:text-gray-800 font-medium transition-colors"
            >
              Maybe Later
            </button>
          </div>

          <p className="text-xs text-center text-gray-500">
            No credit card required • Takes less than a minute
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

