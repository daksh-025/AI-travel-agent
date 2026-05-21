"use client";

import { useState } from 'react';
import { useUser } from '@/app/context/UserContext';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { LogOut, User, Settings, MessageSquare } from 'lucide-react';
import Link from 'next/link';

export default function UserNavMenu() {
  // Add defensive programming for context
  const userContext = useUser();
  const user = userContext?.user || null;
  const logout = userContext?.logout || (() => console.warn('UserProvider not available'));
  
  const [isOpen, setIsOpen] = useState(false);

  if (!user) return null;

  const handleLogout = () => {
    logout();
    setIsOpen(false);
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="hover:bg-transparent flex items-center space-x-2 text-white hover:text-gray-300 transition-colors focus-visible:ring-0 focus-visible:ring-offset-0">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-white text-[#252d63] text-sm font-medium">
              {getInitials(user.username)}
            </AvatarFallback>
          </Avatar>
          <span className="hidden sm:block text-sm font-medium capitalize">{user.username}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user.username}</p>
            <p className="text-xs leading-none text-muted-foreground">
              {user.email}
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/chat" className="flex items-center">
            <MessageSquare className="mr-2 h-4 w-4" />
            <span>Chat</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem>
          <User className="mr-2 h-4 w-4" />
          <span>Profile</span>
        </DropdownMenuItem>
        <DropdownMenuItem>
          <Settings className="mr-2 h-4 w-4" />
          <span>Settings</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleLogout}>
          <LogOut className="mr-2 h-4 w-4" />
          <span>Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
} 