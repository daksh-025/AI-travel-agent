"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

interface Location {
  city: string;
  country: string;
}

interface Preferences {
  adults: string;
  children: string;
  childrenAgeList: string[];
  tripType: string;
  otherTripType: string;
  budget: string;
  budgetType: string;
  minStarRating: string;
  searchPreferences: string[];
}

interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  avatarUrl?: string;
  created_at: string;
  updated_at: string;
  language?: string;
  location?: Location;
  currency?: string;
  preferences?: Preferences;
}

interface UserContextType {
  user: User | null;
  isAuthenticated: boolean;
  logout: () => void;
  updateUser: (userData: User) => void;
  login: (userData: User, rememberMe?: boolean) => void;
  getRemainingSessionTime: () => number; // Returns remaining time in milliseconds
}

const UserContext = createContext<UserContextType | undefined>(undefined);

// Session timeouts in milliseconds
const SESSION_TIMEOUT = 2 * 60 * 60 * 1000; // 2 hours
const REMEMBER_ME_TIMEOUT = 7 * 24 * 60 * 60 * 1000; // 7 days

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  // Check if session has expired
  const isSessionExpired = (): boolean => {
    if (typeof window === 'undefined') return false;
    
    const loginTime = localStorage.getItem('login_time');
    const rememberMe = localStorage.getItem('remember_me') === 'true';
    if (!loginTime) return true;
    
    const loginTimestamp = parseInt(loginTime, 10);
    const currentTime = Date.now();
    const timeElapsed = currentTime - loginTimestamp;
    
    const timeout = rememberMe ? REMEMBER_ME_TIMEOUT : SESSION_TIMEOUT;
    return timeElapsed >= timeout;
  };

  // Save login time and remember me preference to localStorage
  const saveLoginTime = (rememberMe: boolean = false) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('login_time', Date.now().toString());
      localStorage.setItem('remember_me', rememberMe.toString());
    }
  };

  // Check for existing user data on mount
  useEffect(() => {
    const checkExistingUser = () => {
      if (typeof window !== 'undefined') {
        const userData = localStorage.getItem('user_data') || sessionStorage.getItem('user_data');
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
        
        if (userData && token) {
          // Check if session has expired
          if (isSessionExpired()) {
            // console.log('Session expired, logging out user');
            logout();
            return;
          }
          
          try {
            const parsedUser = JSON.parse(userData);
            setUser(parsedUser);
          } catch (error) {
            console.error('Failed to parse user data:', error);
            logout();
          }
        }
      }
    };

    checkExistingUser();
  }, []);

  // Set up periodic session check (every 5 minutes)
  useEffect(() => {
    if (!user) return;

    const sessionCheckInterval = setInterval(() => {
      if (isSessionExpired()) {
        // console.log('Session expired during periodic check, logging out user');
        logout();
      }
    }, 5 * 60 * 1000); // Check every 5 minutes

    return () => clearInterval(sessionCheckInterval);
  }, [user]);

  // Listen for login events
  useEffect(() => {
    const handleUserLogin = (event: CustomEvent) => {
      try {
        if (event.detail && typeof event.detail === 'object') {
          setUser(event.detail);
          // Get remember me preference from the event or default to false
          const rememberMe = event.detail.rememberMe || false;
          saveLoginTime(rememberMe); // Save login time when user logs in
        } else {
          console.warn('Invalid user data received in login event:', event.detail);
        }
      } catch (error) {
        console.error('Error handling user login event:', error);
      }
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('userLoggedIn', handleUserLogin as EventListener);

      return () => {
        window.removeEventListener('userLoggedIn', handleUserLogin as EventListener);
      };
    }
  }, []);

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_data');
      localStorage.removeItem('login_time');
      localStorage.removeItem('remember_me');
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('user_data');
    }
    setUser(null);
  };

  const updateUser = (userData: User) => {
    setUser(userData);
    if (typeof window !== 'undefined') {
      const storage = localStorage.getItem('access_token') ? localStorage : sessionStorage;
      storage.setItem('user_data', JSON.stringify(userData));
    }
  };

  const login = (userData: User, rememberMe: boolean = false) => {
    setUser(userData);
    saveLoginTime(rememberMe);
    if (typeof window !== 'undefined') {
      const storage = localStorage.getItem('access_token') ? localStorage : sessionStorage;
      storage.setItem('user_data', JSON.stringify(userData));
    }
  };

  const getRemainingSessionTime = () => {
    if (typeof window === 'undefined') return 0;
    const loginTime = localStorage.getItem('login_time');
    const rememberMe = localStorage.getItem('remember_me') === 'true';
    if (!loginTime) return 0;
    const loginTimestamp = parseInt(loginTime, 10);
    const currentTime = Date.now();
    const timeElapsed = currentTime - loginTimestamp;
    const timeout = rememberMe ? REMEMBER_ME_TIMEOUT : SESSION_TIMEOUT;
    return Math.max(0, timeout - timeElapsed);
  };

  const value: UserContextType = {
    user,
    isAuthenticated: !!user,
    logout,
    updateUser,
    login,
    getRemainingSessionTime,
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    // Return a default context instead of throwing an error
    console.warn('useUser must be used within a UserProvider');
    return {
      user: null,
      isAuthenticated: false,
      logout: () => console.warn('UserProvider not found'),
      updateUser: () => console.warn('UserProvider not found'),
      login: () => console.warn('UserProvider not found'),
      getRemainingSessionTime: () => 0,
    };
  }
  return context;
} 