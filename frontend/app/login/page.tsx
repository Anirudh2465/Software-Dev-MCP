'use client';

import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button, Input, Card } from '../../components/ui/PremiumComponents';
import axios from 'axios';
import Link from 'next/link';
import { motion } from 'framer-motion';

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const { login } = useAuth();
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const res = await axios.post('http://localhost:8001/auth/login', formData);
            login(res.data.access_token, username);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Login failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[calc(100vh-80px)] flex items-center justify-center p-4 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(to_bottom,white,transparent)]">
            <Card className="w-full max-w-md space-y-8 bg-black/40 border-white/10">
                <div className="text-center">
                    <motion.h2
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-3xl font-bold tracking-tight text-white"
                    >
                        Welcome Back
                    </motion.h2>
                    <p className="mt-2 text-sm text-gray-400">Sign in to your Jarvis account</p>
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

                    <Button type="submit" disabled={loading} className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500">
                        {loading ? "Signing in..." : "Sign in"}
                    </Button>
                </form>

                <div className="text-center text-sm text-gray-500">
                    Don't have an account?{' '}
                    <Link href="/signup" className="font-medium text-blue-400 hover:text-blue-300">
                        Sign up
                    </Link>
                </div>
            </Card>
        </div>
    );
}
