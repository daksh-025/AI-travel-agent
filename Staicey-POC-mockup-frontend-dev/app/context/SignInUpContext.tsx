'use client'

import React, { createContext, useState, useContext, ReactNode, useEffect } from 'react';

// Define the type for the context's value
interface SignInUpContextType {
  isPopupOpen: boolean;
  openPopup: (searchQuery?: string) => void;
  closePopup: () => void;
  isSignInOr: boolean;
  goSignIn: () => void;
  goSignUp: () => void;
  pendingSearchQuery: string | null;
  clearPendingSearchQuery: () => void;
  pendingSearchLoading: boolean;
  setPendingSearchLoading: (loading: boolean) => void;
}

// Create the context with a default value (or undefined)
const SignInUpContext = createContext<SignInUpContextType | undefined>(undefined);

// Define the type for the provider's props
interface SignInUpProviderProps {
  children: ReactNode;
}

// Create the provider component
export const SignInUpProvider = ({ children }: SignInUpProviderProps) => {
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  const [isSignInOr, setIsSignInOr] = useState(true);
  const [pendingSearchQuery, setPendingSearchQuery] = useState<string | null>(null);
  const [pendingSearchLoading, setPendingSearchLoading] = useState(false);

  useEffect(() => {
    if (isPopupOpen) {
      // When the popup is open, add the 'no-scroll' class to the body
      document.body.classList.add('no-scroll');
    } else {
      // When the popup is closed, remove the 'no-scroll' class
      document.body.classList.remove('no-scroll');
    }

    // Cleanup function: ensures the class is removed if the component unmounts
    return () => {
      document.body.classList.remove('no-scroll');
    };
  }, [isPopupOpen]);

  // const openPopup = () => setIsPopupOpen(true);
  const openPopup= (searchQuery?: string) => {
    setIsPopupOpen(true)
    if (searchQuery) {
      setPendingSearchQuery(searchQuery);
    }
  }
  const closePopup = () => {
    setPendingSearchQuery(null)
    setIsPopupOpen(false);
  }

  const goSignUp = () => setIsSignInOr(false)
  const goSignIn = () => setIsSignInOr(true)

  const clearPendingSearchQuery = () => {
    setPendingSearchQuery(null);
  };

  const value = { isPopupOpen, openPopup, closePopup, isSignInOr, goSignIn, goSignUp, pendingSearchQuery, clearPendingSearchQuery, pendingSearchLoading, setPendingSearchLoading };

  return (
    <SignInUpContext.Provider value={value}>
      {children}
    </SignInUpContext.Provider>
  );
};

// Create a custom hook for easy consumption
export const useSignInUp = (): SignInUpContextType | null => {
  const context = useContext(SignInUpContext);
  if (context === undefined) {
    // Return null instead of a default context to make the error more obvious
    console.warn('useSignInUp must be used within a SignInUpProvider');
    return null;
  }
  return context;
};