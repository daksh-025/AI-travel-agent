"use client";

import { useState, useEffect } from 'react';
import { useUser } from '@/app/context/UserContext';
import { AlertTriangle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

const SessionTimeoutWarning = () => {
  const { user, logout, getRemainingSessionTime } = useUser();
  const [showWarning, setShowWarning] = useState(false);
  const [remainingTime, setRemainingTime] = useState(0);

  useEffect(() => {
    if (!user) return;

    const checkSessionTime = () => {
      const remaining = getRemainingSessionTime();
      setRemainingTime(remaining);
      
      // Show warning when less than 10 minutes remaining
      if (remaining > 0 && remaining < 10 * 60 * 1000) {
        setShowWarning(true);
      } else {
        setShowWarning(false);
      }
    };

    // Check immediately
    checkSessionTime();

    // Check every minute
    const interval = setInterval(checkSessionTime, 60 * 1000);

    return () => clearInterval(interval);
  }, [user, getRemainingSessionTime]);

  const formatTime = (milliseconds: number) => {
    const minutes = Math.floor(milliseconds / (1000 * 60));
    const seconds = Math.floor((milliseconds % (1000 * 60)) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const handleExtendSession = () => {
    // This would typically make an API call to refresh the session
    // For now, we'll just hide the warning
    setShowWarning(false);
  };

  const handleLogout = () => {
    logout();
    setShowWarning(false);
  };

  if (!showWarning || !user) return null;

  return (
    <div className="fixed top-4 right-4 z-50 bg-yellow-50 border border-yellow-200 rounded-lg p-4 shadow-lg max-w-sm">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="text-sm font-medium text-yellow-800">
            Session Expiring Soon
          </h3>
          <p className="text-sm text-yellow-700 mt-1">
            Your session will expire in {formatTime(remainingTime)}. Please save your work.
          </p>
          <div className="flex gap-2 mt-3">
            {/* <Button
              size="sm"
              variant="outline"
              onClick={handleExtendSession}
              className="text-xs"
            >
              Stay Logged In
            </Button> */}
            <Button
              size="sm"
              variant="destructive"
              onClick={handleLogout}
              className="text-xs"
            >
              Logout Now
            </Button>
          </div>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setShowWarning(false)}
          className="text-yellow-600 hover:text-yellow-800 p-1 h-auto"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};

export default SessionTimeoutWarning;
