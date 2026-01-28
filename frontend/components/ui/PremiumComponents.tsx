import React from 'react';
import { motion } from 'framer-motion';

export const Button = ({ children, onClick, className = "", type = "button", disabled = false }: any) => {
    return (
        <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type={type}
            onClick={onClick}
            disabled={disabled}
            className={`px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
        >
            {children}
        </motion.button>
    );
};

export const Input = ({ value, onChange, placeholder, type = "text", className = "" }: any) => {
    return (
        <input
            type={type}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            className={`w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all backdrop-blur-sm ${className}`}
        />
    );
};

export const Card = ({ children, className = "" }: any) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-6 shadow-2xl ${className}`}
        >
            {children}
        </motion.div>
    );
};
