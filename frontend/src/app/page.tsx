'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Image from "next/image";

export default function Home() {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user) {
      // If user is logged in, redirect to dashboard
      router.push('/dashboard');
    } else {
      // If user is not logged in, redirect to login
      router.push('/login');
    }
  }, [user, router]);

  // Show loading while determining redirect
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
}
