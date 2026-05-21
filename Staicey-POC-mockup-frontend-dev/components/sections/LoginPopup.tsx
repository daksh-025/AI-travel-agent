"use client"

import {useState, useEffect} from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Plane, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useSignInUp } from '@/app/context/SignInUpContext';
import { useUser } from '@/app/context/UserContext';
import { useRouter } from 'next/navigation';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Signin schema
const signinSchema = z.object({
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(1, 'Password is required'),
});

// Signup schema
const signupSchema = z.object({
  email: z.string().email('Please enter a valid email'),
  username: z.string().min(2, 'First Name must be at least 2 characters'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

// Forgot password schema
const forgotSchema = z.object({
  email: z.string().email('Please enter a valid email'),
});

type SigninForm = z.infer<typeof signinSchema>;
type SignupForm = z.infer<typeof signupSchema>;
type ForgotForm = z.infer<typeof forgotSchema>;

interface AuthResponse {
  access_token: string;
  token_type: string;
}

interface UserResponse {
  email: string;
  username: string;
  id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export default function LoginPopup() {
  // Add defensive programming for context
  const signInUpContext = useSignInUp();
  const userContext = useUser();
  const router = useRouter();
  
  // Ensure we have a valid context before destructuring
  if (!signInUpContext) {
    console.warn('LoginPopup: SignInUpProvider not available');
    return null;
  }

  const {isPopupOpen, closePopup, isSignInOr, goSignUp, goSignIn, pendingSearchQuery, clearPendingSearchQuery, pendingSearchLoading, setPendingSearchLoading} = signInUpContext;
  const { login } = userContext;

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isForgot, setIsForgot] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  // Add defensive check for isSignInOr and ensure it's a boolean
  const currentSchema = (isSignInOr === true) ? signinSchema : signupSchema;

  const form = useForm<SigninForm | SignupForm>({
    resolver: zodResolver(currentSchema),
    mode: 'onChange',
    defaultValues: isSignInOr ? { email: '', password: '' } : { email: '', username: '', password: '' }
  });

  // Separate form for forgot-password to avoid dynamic resolver issues
  const forgotForm = useForm<ForgotForm>({
    resolver: zodResolver(forgotSchema),
    mode: 'onChange',
    defaultValues: { email: '' }
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    setFocus
  } = form;

  const {
    register: registerForgot,
    handleSubmit: handleSubmitForgot,
    formState: { errors: errorsForgot, isSubmitting: isSubmittingForgot },
    reset: resetForgot,
    setFocus: setFocusForgot
  } = forgotForm;

  // Focus email input when popup opens for better UX
  useEffect(() => {
    if (isPopupOpen && typeof isSignInOr === 'boolean' && !isForgot) {
      // Defer to next tick to ensure the input is mounted
      const id = setTimeout(() => {
        try {
          setFocus('email' as any);
        } catch {}
      }, 0);
      return () => clearTimeout(id);
    }
  }, [isPopupOpen, isSignInOr, isForgot, setFocus]);

  // Focus for forgot password form
  useEffect(() => {
    if (isPopupOpen && isForgot) {
      const id = setTimeout(() => {
        try {
          setFocusForgot('email' as any);
        } catch {}
      }, 0);
      return () => clearTimeout(id);
    }
  }, [isPopupOpen, isForgot, setFocusForgot]);

  // Early return if popup is not open or if context is invalid
  if (!isPopupOpen || typeof isSignInOr !== 'boolean') {
    return null;
  }

  // Store token and user data based on Remember me
  const setUserData = (token: string, userData: any) => {
    if (typeof window !== 'undefined') {
      try {
        // Clear previous storage to avoid stale tokens across storages
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('user_data');
        const storage = rememberMe ? localStorage : sessionStorage;
        storage.setItem('access_token', token);
        storage.setItem('user_data', JSON.stringify(userData));
      } catch {}
    }
  };

  // API request helper
  const apiRequest = async (endpoint: string, data: any) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  };

  // Forgot password API
  const requestPasswordReset = async (email: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  };

  // Get user data after login
  const getUserData = async (token: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user data, please try again.');
    }

    return response.json();
  };

  const handleSignin = async (data: SigninForm) => {
    try {
      setError('');
      setSuccess('');
      
      const response: AuthResponse = await apiRequest('/auth/login', {
        email: data.email,
        password: data.password,
        remember_me: rememberMe,
      });

      // Get user data after successful login
      const userData = await getUserData(response.access_token);
      
      // Store the token and user data
      setUserData(response.access_token, userData);
      
      // Use UserContext login function to set user and save login time
      login(userData, rememberMe);
      
      setSuccess('Login successful!');
      
      // Close popup after a short delay
      setTimeout(async () => {
        closePopup();
        reset();
        setSuccess('');
        
        // If there's a pending search query, create a new chat and send the query
        if (pendingSearchQuery) {
          setPendingSearchLoading(true);
          try {
            // Create a new chat tab
            const createTabResponse = await fetch(`${API_BASE_URL}/chat/tabs`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${response.access_token}`,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                title: "New Chat",
              }),
            });

            if (createTabResponse.ok) {
              const newTab = await createTabResponse.json();
              
              // Send the pending search query
              const messageResponse = await fetch(`${API_BASE_URL}/chat/message`, {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${response.access_token}`,
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  message: pendingSearchQuery,
                  tab_id: newTab.tab_id,
                }),
              });

              if (messageResponse.ok) {
                // Navigate to the new chat
                router.push(`/chat/${newTab.tab_id}`);
              } else {
                // If message sending fails, just navigate to the new chat
                router.push(`/chat/${newTab.tab_id}`);
              }
            } else {
              // If tab creation fails, navigate to main chat page
              router.push('/chat');
            }
          } catch (err) {
            console.error('Failed to create chat with pending query:', err);
            router.push('/chat');
          } finally {
            setPendingSearchLoading(false);
          }
          
          // Clear the pending search query
          clearPendingSearchQuery();
        } else {
          // No pending query, just navigate to chat page
          router.push('/chat');
        }
        
        // Trigger a custom event to notify other components about login
        window.dispatchEvent(new CustomEvent('userLoggedIn', { detail: { ...userData, rememberMe } }));
      }, 1500);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.');
    }
  };

  const handleSignup = async (data: SignupForm) => {
    try {
      setError('');
      setSuccess('');
      
      // Generate username from email if username is empty
      const username = data.username.trim() || data.email.split('@')[0];
      
      const response: UserResponse = await apiRequest('/auth/signup', {
        email: data.email,
        username: username,
        password: data.password,
      });

      setSuccess('Account created successfully! Logging you in...');
      
      // Automatically log in with the same credentials
      try {
        const loginResponse: AuthResponse = await apiRequest('/auth/login', {
          email: data.email,
          password: data.password,
          remember_me: rememberMe,
        });

        // Get user data after successful login
        const userData = await getUserData(loginResponse.access_token);
        
        // Store the token and user data
        setUserData(loginResponse.access_token, userData);
        
        // Use UserContext login function to set user and save login time
        login(userData, rememberMe);
        
        // Close popup and redirect after successful auto-login
        setTimeout(async () => {
          closePopup();
          reset();
          setSuccess('');
          
          // If there's a pending search query, create a new chat and send the query
        if (pendingSearchQuery) {
          setPendingSearchLoading(true);
          try {
            // Create a new chat tab
            const createTabResponse = await fetch(`${API_BASE_URL}/chat/tabs`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${loginResponse.access_token}`,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                title: "New Chat",
              }),
            });

            if (createTabResponse.ok) {
              const newTab = await createTabResponse.json();
              
              // Send the pending search query
              const messageResponse = await fetch(`${API_BASE_URL}/chat/message`, {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${loginResponse.access_token}`,
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  message: pendingSearchQuery,
                  tab_id: newTab.tab_id,
                }),
              });

              if (messageResponse.ok) {
                // Navigate to the new chat
                router.push(`/chat/${newTab.tab_id}`);
              } else {
                // If message sending fails, just navigate to the new chat
                router.push(`/chat/${newTab.tab_id}`);
              }
            } else {
              // If tab creation fails, navigate to main chat page
              router.push('/chat');
            }
          } catch (err) {
            console.error('Failed to create chat with pending query:', err);
            router.push('/chat');
          } finally {
            setPendingSearchLoading(false);
          }
          
          // Clear the pending search query
          clearPendingSearchQuery();
        } else {
          // No pending query, just navigate to chat page
          router.push('/chat');
        }
        
        // Trigger a custom event to notify other components about login
        window.dispatchEvent(new CustomEvent('userLoggedIn', { detail: { ...userData, rememberMe } }));
        }, 1500);

      } catch (loginErr) {
        // If auto-login fails, show success message and switch to signin form
        setSuccess('Account created successfully! Please sign in.');
        setTimeout(() => {
          goSignIn();
          reset();
          setSuccess('');
        }, 1500);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed. Please try again.');
    }
  };

  const onSubmit = async (data: SigninForm | SignupForm) => {
    if (isSignInOr) {
      await handleSignin(data as SigninForm);
    } else {
      await handleSignup(data as SignupForm);
    }
  };

  const onSubmitForgot = async (data: ForgotForm) => {
    try {
      setError('');
      setSuccess('');
      await requestPasswordReset(data.email);
      setSuccess('If that email exists, a reset link has been sent.');
      resetForgot();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed. Please try again.');
    }
  };

  const clickGoSignIn = (e : React.MouseEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    reset();
    setIsForgot(false);
    if(isSignInOr) {
      goSignUp();
    } else {
      goSignIn();
    }
  }

  return (
      <div className="fixed min-h-screen w-full bg-black bg-opacity-50 flex items-center justify-center p-4 z-10">
        <div className="inset-0 "></div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="relative w-full max-w-[370px]"
        >
          <div className="bg-white w-full rounded-3xl p-8 shadow-2xl border border-white/20 relative z-10">
            <div className="absolute top-0 left-0 w-full h-full login-popup-bg z-0"></div>
            {/* Header */}
            <div className='flex justify-between'>
              <div className="mb-8">
                <h1 className="text-2xl font-bold  mb-2">{isSignInOr ? "Login" : "Sign up"}</h1>
              </div>
              <button className="mb-8 text-black/70 hover:text-black text-xl z-10" onClick={closePopup}>
                &times;
              </button>
            </div>

            {/* Error/Success Messages */}
            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
                {error}
              </div>
            )}
            
            {success && (
              <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded text-sm">
                {success}
              </div>
            )}
  
            {/* Forms */}
            {!isForgot && (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 z-10">
              {!isSignInOr && (
                <div className='relative z-10'>
                  <Input
                    id="username"
                    type="text"
                    {...register('username' as any)}
                    className="mt-2 bg-white/10 border-black/20 border rounded-none h-12 py-4 placeholder:text-gray-300 focus:outline-none z-10"
                    placeholder="First Name *"
                  />
                  {!isSignInOr && (errors as any).username && (
                    <p className="mt-1 text-sm text-red-300">{(errors as any).username?.message}</p>
                  )}
                </div>
              )}

              <div className='relative z-10'> 
                <Input
                  id="email"
                  type="email"
                  autoComplete='email'
                  {...register('email' as any)}
                  className="mt-2 bg-white/10 border-black/20 border rounded-none h-12 py-4 placeholder:text-gray-300 focus:outline-none z-10"
                  placeholder="Email Address *"
                />
                {errors.email && (
                  <p className="mt-1 text-sm text-red-300">{errors.email.message}</p>
                )}
              </div>
  
              <div>
                <div className="relative mt-2">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    {...register('password' as any)}
                    className="bg-white/10 border-black/20 h-12 rounded-none py-4 placeholder:text-gray-300 pr-12"
                    placeholder="Password *"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-300 hover:"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="mt-1 text-sm text-red-300">{errors.password.message}</p>
                )}
                {isSignInOr && (
                  <div className="flex justify-between relative mt-2 text-xs z-10">
                    <label className="flex items-center gap-2 text-xs text-[#252d63] font-semibold">
                      <input
                        type="checkbox"
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                      />
                      Remember me
                    </label>
                    <button
                      type="button"
                      className="underline text-[#252d63] font-semibold"
                      onClick={() => {
                        setError('');
                        setSuccess('');
                        setIsForgot(true);
                      }}
                    >
                      Forgot password?
                    </button>
                  </div>
                )}
              </div>
  
              <div className='flex flex-col sm:flex-row gap-3 align-center items-center justify-between text-black'>
                <div className=" flex flex-col z-10" style={{fontSize: 12}}>
                  <p className="w-full">
                    {
                      isSignInOr ? "Don't have an account? "  : "Already have an account? "
                    }
                  </p>
                  <div className="p-0 m-0 bg-transparent underline text-[#252d63] text-left block font-semibold w-full cursor-pointer" onClick={clickGoSignIn}>
                    {
                      isSignInOr ? "Click here to create one" : "Click here to go to login"
                    }
                  </div>
                </div>
                <Button
                  style={{
                    backgroundImage: 'linear-gradient(135deg, #4f2f78 0%, #3e50a3 55%, #252d63 100%)'
                  }}
                  type="submit"
                  disabled={isSubmitting}
                  className=" text-white hover:bg-gray-100 font-semibold py-3 px-12 max-w-[142px] rounded-full z-10"
                >
                  {
                    isSignInOr ? isSubmitting ? 'Signing In...' : 'Sign In'
                               : isSubmitting ? 'Signing Up...' : 'Sign Up'
                  }
                  
                </Button>
                
              </div>
              
            </form>
            )}

            {isForgot && (
            <form onSubmit={handleSubmitForgot(onSubmitForgot)} className="space-y-6 z-10">
              <div className='relative z-10'> 
                <Input
                  id="forgot-email"
                  type="email"
                  autoComplete='email'
                  {...registerForgot('email' as any)}
                  className="mt-2 bg-white/10 border-black/20 border rounded-none h-12 py-4 placeholder:text-gray-300 focus:outline-none z-10"
                  placeholder="Email Address *"
                />
                {errorsForgot.email && (
                  <p className="mt-1 text-sm text-red-300">{errorsForgot.email.message as any}</p>
                )}
              </div>

              <div className='flex flex-col sm:flex-row gap-3 align-center items-center justify-between text-black'>
                <div className=" flex flex-col z-10" style={{fontSize: 12}}>
                  <button
                    type="button"
                    className="p-0 m-0 bg-transparent underline text-[#252d63] text-left block font-semibold w-full cursor-pointer"
                    onClick={() => {
                      setIsForgot(false);
                      setError('');
                      setSuccess('');
                    }}
                  >
                    Back to login
                  </button>
                </div>
                <Button
                  style={{
                    backgroundImage: 'linear-gradient(135deg, #4f2f78 0%, #3e50a3 55%, #252d63 100%)'
                  }}
                  type="submit"
                  disabled={isSubmittingForgot}
                  className=" text-white hover:bg-gray-100 font-semibold py-3 px-12 max-w-[180px] rounded-full z-10"
                >
                  {isSubmittingForgot ? 'Sending...' : 'Send reset link'}
                </Button>
              </div>
            </form>
            )}
  
            {/* Footer */}
            
          </div>
        </motion.div>
      </div>
    )
}