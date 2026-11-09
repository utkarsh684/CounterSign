import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect, createContext, useContext } from 'react';
import { AnimatePresence } from 'framer-motion';
import Layout from './components/Layout';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Mandates from './pages/Mandates';
import Payees from './pages/Payees';
import Invoices from './pages/Invoices';
import Gateway from './pages/Gateway';
import Approvals from './pages/Approvals';
import AuditLedger from './pages/AuditLedger';
import RedTeam from './pages/RedTeam';
import PayPalStatus from './pages/PayPalStatus';
import SecurityPanel from './pages/SecurityPanel';
import './index.css';

import type { User } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30_000,
    },
  },
});

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  login: () => {},
  logout: () => {},
  isAuthenticated: false,
});

export const useAuth = () => useContext(AuthContext);

function App() {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('countersign_user');
    return stored ? JSON.parse(stored) : null;
  });
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('countersign_token')
  );

  const login = (newToken: string, newUser: User) => {
    localStorage.setItem('countersign_token', newToken);
    localStorage.setItem('countersign_user', JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    localStorage.removeItem('countersign_token');
    localStorage.removeItem('countersign_user');
    setToken(null);
    setUser(null);
  };

  const isAuthenticated = !!token && !!user;

  return (
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated }}>
        <BrowserRouter>
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Login />} />
              <Route path="/register" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Register />} />
              <Route element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/mandates" element={<Mandates />} />
                <Route path="/payees" element={<Payees />} />
                <Route path="/invoices" element={<Invoices />} />
                <Route path="/gateway" element={<Gateway />} />
                <Route path="/approvals" element={<Approvals />} />
                <Route path="/audit" element={<AuditLedger />} />
                <Route path="/red-team" element={<RedTeam />} />
                <Route path="/paypal" element={<PayPalStatus />} />
                <Route path="/security" element={<SecurityPanel />} />
              </Route>
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </AnimatePresence>
        </BrowserRouter>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}

export default App;
