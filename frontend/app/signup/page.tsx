'use client';

import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button, Input, Card } from '../../components/ui/PremiumComponents';
import axios from 'axios';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';

export default function SignupPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const router = useRouter();
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        try {
            await axios.post('http://localhost:8001/auth/signup', { username, password });
            // Auto login or redirect to login
            router.push('/login');
        } catch (err: any) {
            setError(err.response?.data?.detail || "Signup failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[calc(100vh-80px)] flex items-center justify-center p-4">
            <div className="absolute inset-0 -z-10 h-full w-full items-center px-5 py-24 [background:radial-gradient(125%_125%_at_50%_10%,#000_40%,#63e_100%)] opacity-50"></div>
            <Card className="w-full max-w-md space-y-8 bg-black/40 border-white/10">
                <div className="text-center">
                    <motion.h2
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-3xl font-bold tracking-tight text-white"
                    >
                        Create Account
                    </motion.h2>
                    <p className="mt-2 text-sm text-gray-400">Join the future with Jarvis</p>
                </div>

                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    <div className="space-y-4">
                        <Input
                            placeholder="Username"
                            value={username}
                            onChange={(e: any) => setUsername(e.target.value)}
                        />
                        <Input
                            placeholder="Password"
                            type="password"
                            value={password}
                            onChange={(e: any) => setPassword(e.target.value)}
                        />
                    </div>

                    {error && <p className="text-red-400 text-sm text-center">{error}</p>}

                    <Button type="submit" disabled={loading} className="w-full">
                        {loading ? "Creating..." : "Sign up"}
                    </Button>
                </form>

                <div className="text-center text-sm text-gray-500">
                    Already have an account?{' '}
                    <Link href="/login" className="font-medium text-blue-400 hover:text-blue-300">
                        Sign in
                    </Link>
                </div>
            </Card>
        </div>
    );
}
