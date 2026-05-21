'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { Menu, X, Plane } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useSignInUp } from '@/app/context/SignInUpContext';
import { useUser } from '@/app/context/UserContext';
import UserNavMenu from '../auth/UserNavMenu';
import LoginPopup from '../sections/LoginPopup';

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isBlur, setIsBlur] = useState(false);
  
  // Add defensive programming for contexts
  const signInUpContext = useSignInUp();
  const userContext = useUser();

  const openPopup = signInUpContext?.openPopup || (() => console.warn('SignInUpProvider not available'));
  const user = userContext?.user || null;
  const isAuthenticated = userContext?.isAuthenticated || false;

  const handleLoginClick = () => {
    if(isMenuOpen) setIsMenuOpen(false);
    openPopup();
  };

  useEffect(() => {
    const handleScroll = () => {
      setIsBlur(window.scrollY > 100);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  
  return (
    <>
      <LoginPopup />
      <header className={`fixed top-0 left-0 right-0 z-50 ${isBlur ? 'bg-[#252d63] backdrop-blur-md bg-opacity-80' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-4">
            <Link href="/" className="flex items-center space-x-2">
              <div className=" w-32 h-10 bg-transparent flex items-center justify-center">
                <Image 
                  src="/assets/images/logos/staicey-logo-white.png" 
                  alt="Staicey Logo" 
                  width="132"
                  height="36"
                  style={{height: 'auto', width: '100%'}}
                />
              </div>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8 lg:space-x-14 text-white">
            <div className="hover:text-gray-300 transition-colors cursor-pointer">About</div>
            <div className="hover:text-gray-300 transition-colors cursor-pointer">Features</div>
            {/* <Link href="/questions">
              <div className="hover:text-gray-300 transition-colors cursor-pointer">Questions</div>
            </Link> */}
            <div className="bg-gradient-to-br from-[#4f2f78] via-[#3e50a3] to-[#252d63] text-white px-8 py-3 font-semibold rounded-full hover:opacity-90 transition-opacity cursor-pointer" style={{fontSize: 14}}>Get Started</div>
            {isAuthenticated && (<Link href="/chat">
              <div className="hover:text-gray-300 transition-colors cursor-pointer">Chat History</div>
            </Link>)}
            {isAuthenticated ? (
              <UserNavMenu/>
            ) : (
              <button className="hover:text-gray-300 transition-colors cursor-pointer" onClick={handleLoginClick}>Login</button>
            )}
          </div>

          {/* Mobile Hamburger Button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-white p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="md:hidden bg-black/50 backdrop-blur-md border-t border-white/10"
          >
            <div className="px-4 py-6 space-y-4">
              <div className="text-white hover:text-gray-300 transition-colors cursor-pointer py-2 px-6">About</div>
              <div className="text-white hover:text-gray-300 transition-colors cursor-pointer py-2 px-6">Features</div>
              <div className="bg-gradient-to-br from-[#4f2f78] via-[#3e50a3] to-[#252d63] text-white px-4 py-2 rounded-full inline-block hover:opacity-90 transition-opacity cursor-pointer">Get Started</div>
              {isAuthenticated && (<Link href="/chat">
                <div className="text-white hover:text-gray-300 transition-colors cursor-pointer py-2 mt-4 px-4">Chat History</div>
              </Link>)}
              {isAuthenticated ? (
                <div className="flex items-center">
                  <UserNavMenu />
                </div>
              ) : (
                <div className="w-full space-x-2 px-6"  onClick={handleLoginClick}>
                  <button className="text-white hover:text-gray-300 transition-colors cursor-pointer py-2">Login</button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </header>
    </>
  );
}