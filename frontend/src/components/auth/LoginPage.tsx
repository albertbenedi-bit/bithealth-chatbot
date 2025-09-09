import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Alert, AlertDescription } from '../ui/alert';
import { Loader2, Heart, Shield, Users } from 'lucide-react';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { authState, login, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/';

  useEffect(() => {
    if (authState.isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [authState.isAuthenticated, navigate, from]);

  useEffect(() => {
    if (authState.error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [authState.error, clearError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    await login({ email, password });
  };

  const handleDemoLogin = (role: 'patient' | 'admin') => {
    const demoCredentials = {
      patient: { email: 'patient@demo.com', password: 'demo123' },
      admin: { email: 'admin@demo.com', password: 'admin123' },
    };
    
    setEmail(demoCredentials[role].email);
    setPassword(demoCredentials[role].password);
    login(demoCredentials[role]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center space-x-2">
            <Heart className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">PV Chatbot</h1>
          </div>
          <p className="text-gray-600">Healthcare Assistant Platform</p>
        </div>

        <Card className="shadow-lg">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center">Sign In</CardTitle>
            <CardDescription className="text-center">
              Enter your credentials to access the healthcare chatbot
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {authState.error && (
              <Alert variant="destructive">
                <AlertDescription>{authState.error}</AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium text-gray-700">
                  Email
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={authState.loading}
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium text-gray-700">
                  Password
                </label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={authState.loading}
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={authState.loading || !email || !password}
              >
                {authState.loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing In...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-2 text-gray-500">Demo Access</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Button
                variant="outline"
                onClick={() => handleDemoLogin('patient')}
                disabled={authState.loading}
                className="flex items-center space-x-2"
              >
                <Users className="h-4 w-4" />
                <span>Patient Demo</span>
              </Button>
              <Button
                variant="outline"
                onClick={() => handleDemoLogin('admin')}
                disabled={authState.loading}
                className="flex items-center space-x-2"
              >
                <Shield className="h-4 w-4" />
                <span>Admin Demo</span>
              </Button>
            </div>

            <div className="text-center text-sm text-gray-500">
              <p>Demo authentication always succeeds</p>
              <p className="mt-1">Real auth service integration coming soon</p>
            </div>
          </CardContent>
        </Card>

        <div className="text-center text-xs text-gray-500">
          <p>Secure healthcare communication platform</p>
          <p>© 2024 PV Chatbot. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}
