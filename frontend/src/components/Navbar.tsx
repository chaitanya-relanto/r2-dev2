'use client';

import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';
import Image from 'next/image';
import { ThemeToggleButton } from './ThemeToggleButton';
import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';

export default function Navbar() {
  const { user, logout } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isAvatarDropdownOpen, setIsAvatarDropdownOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [userInfo, setUserInfo] = useState<{ name?: string; email?: string } | null>(null);
  const pathname = usePathname();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Fetch user info when component mounts and user is available
  useEffect(() => {
    const fetchUserInfo = async () => {
      if (!user) return;
      
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/data/users/${user.user_id}/info`);
        
        if (response.ok) {
          const userData = await response.json();
          setUserInfo({
            name: userData.name,
            email: userData.email
          });
        } else {
          // Fallback to user context data
          setUserInfo({
            name: user.email?.split('@')[0], // Use email username as fallback name
            email: user.email
          });
        }
      } catch (error) {
        console.error('Error fetching user info:', error);
        // Fallback to user context data
        setUserInfo({
          name: user.email?.split('@')[0],
          email: user.email
        });
      }
    };

    if (user) {
      fetchUserInfo();
    }
  }, [user]);

  const handleLogout = () => {
    logout();
    setIsDropdownOpen(false);
    setIsAvatarDropdownOpen(false);
  };

  // Generate user initials
  const getUserInitials = () => {
    if (userInfo?.name) {
      return userInfo.name
        .split(' ')
        .map(word => word[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }
    if (userInfo?.email) {
      return userInfo.email[0].toUpperCase();
    }
    return 'U';
  };

  // Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return (
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
        <div className="mx-auto max-w-7xl">
          <div className="flex justify-between items-center px-6 py-3">
            <Link href="/" className="flex items-center">
              <div className="w-10 h-10 mr-3 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
              <span className="text-xl font-bold ml-4 text-gray-900 dark:text-gray-100">
                R2-Dev2
              </span>
            </Link>
            <div className="flex items-center gap-x-4">
              <div className="h-9 w-9 p-2"></div>
            </div>
          </div>
        </div>
      </header>
    );
  }

  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
      <div className="mx-auto max-w-7xl">
        <div className="flex items-center justify-between px-6 py-3">
          {/* Left side - Branding + Navigation */}
          <div className="flex items-center gap-x-8">
            {/* Branding */}
            <Link href="/" className="flex items-center">
              <Image
                src="/logo.png"
                alt="R2Dev2 Logo"
                width={40}
                height={40}
                className="mr-3 rounded-full"
              />
              <span className="text-xl font-bold text-gray-900 dark:text-gray-100">
                R2-Dev2
              </span>
            </Link>
            
            {/* Navigation tabs */}
            {user && (
              <nav className="hidden md:flex items-center gap-x-2">
                <Link
                  href="/dashboard"
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                    pathname === '/dashboard'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  📊 Dashboard
                </Link>
                <Link
                  href="/chat"
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                    pathname === '/chat'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  💬 Chat
                </Link>
              </nav>
            )}
          </div>
          
          {/* Right side - Theme toggle + User avatar */}
          <div className="flex items-center gap-x-4">
            {user ? (
              <>
                {/* Desktop view */}
                <div className="hidden md:flex items-center gap-x-4">
                  <ThemeToggleButton />
                  
                  {/* User Avatar Dropdown */}
                  <div className="relative">
                    <button
                      onClick={() => setIsAvatarDropdownOpen(!isAvatarDropdownOpen)}
                      className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
                    >
                      {getUserInitials()}
                    </button>
                    
                    {/* Avatar Dropdown */}
                    {isAvatarDropdownOpen && (
                      <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50">
                        {/* User Info */}
                        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-blue-600 text-white font-semibold flex items-center justify-center">
                              {getUserInitials()}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                {userInfo?.name || 'User'}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                                {userInfo?.email || user.email || 'user@example.com'}
                              </p>
                            </div>
                          </div>
                        </div>
                        
                        {/* Dropdown Actions */}
                        <div className="py-1">
                          <button
                            onClick={handleLogout}
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200 flex items-center gap-2"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                            </svg>
                            Logout
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Mobile view - Dropdown */}
                <div className="md:hidden relative">
                  <div className="flex items-center gap-x-2">
                    <ThemeToggleButton />
                    <button
                      onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                      className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white focus:outline-none"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                      </svg>
                    </button>
                  </div>
                  
                  {/* Mobile Dropdown menu */}
                  {isDropdownOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50">
                      <Link
                        href="/dashboard"
                        className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
                        onClick={() => setIsDropdownOpen(false)}
                      >
                        📊 Dashboard
                      </Link>
                      <Link
                        href="/chat"
                        className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
                        onClick={() => setIsDropdownOpen(false)}
                      >
                        💬 Chat
                      </Link>
                      <div className="border-t border-gray-200 dark:border-gray-700 my-2"></div>
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center gap-x-4">
                <ThemeToggleButton />
                <Link 
                  href="/login" 
                  className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors duration-200"
                >
                  Login
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Overlays for dropdowns */}
      {(isDropdownOpen || isAvatarDropdownOpen) && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => {
            setIsDropdownOpen(false);
            setIsAvatarDropdownOpen(false);
          }}
        />
      )}
    </header>
  );
} 