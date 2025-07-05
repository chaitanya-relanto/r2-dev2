'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export function ThemeToggleButton() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleTheme = () => {
    if (mounted) {
      setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
    }
  };

  if (!mounted) {
    // Render a consistent placeholder that matches the final button size
    return (
      <div className="relative group">
        <div className="inline-flex items-center justify-center p-2 rounded-md text-gray-600 dark:text-gray-300 h-9 w-9">
          <span className="text-lg">🌙</span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative group">
      <button
        onClick={toggleTheme}
        className="inline-flex items-center justify-center p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 focus:outline-none transition-colors duration-200"
        title={resolvedTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        <span className="sr-only">Toggle theme</span>
        <span className="text-lg">
          {resolvedTheme === 'dark' ? '☀️' : '🌙'}
        </span>
      </button>
      
      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs text-white bg-gray-900 dark:bg-gray-700 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap">
        {resolvedTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      </div>
    </div>
  );
} 