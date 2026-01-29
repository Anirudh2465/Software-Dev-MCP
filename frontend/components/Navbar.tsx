'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '../app/context/AuthContext';
import { Button } from './ui/PremiumComponents';
import { usePathname } from 'next/navigation';

export const Navbar = () => {
    const { user, logout } = useAuth();
    const pathname = usePathname();

    // Don't show navbar on login/signup pages if you want a clean look, 
    // currently showing it for navigation ease but can hide.
    if (pathname === '/login' || pathname === '/signup') return null;

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-4 bg-black/20 backdrop-blur-lg border-b border-white/10">
            <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent hover:scale-105 transition-transform">
                Jarvis
            </Link>

            {user && (
                <div className="flex items-center gap-6">
                    <Link href="/" className={`text-sm font-medium transition-colors ${pathname === '/' ? 'text-blue-400' : 'text-gray-400 hover:text-white'}`}>
                        Chat
                    </Link>
                    <Link href="/memory" className={`text-sm font-medium transition-colors ${pathname === '/memory' ? 'text-blue-400' : 'text-gray-400 hover:text-white'}`}>
                        Memory
                    </Link>
                    <div className="h-4 w-px bg-white/10 mx-2" />
                    <span className="text-sm text-gray-400">Hello, <span className="text-white font-semibold">{user.username}</span></span>
                    <Button onClick={logout} className="!px-4 !py-2 !text-sm !bg-none !bg-white/10 hover:!bg-white/20">
                        Logout
                    </Button>
                </div>
            )}
        </nav>
    );
};
