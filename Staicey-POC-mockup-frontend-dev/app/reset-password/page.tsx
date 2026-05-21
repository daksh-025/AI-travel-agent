"use client";

 import { useEffect, useState } from 'react';
 import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import Image from 'next/image';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const schema = z.object({
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string().min(8, 'Confirm password must be at least 8 characters'),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

type ResetForm = z.infer<typeof schema>;

 export default function ResetPasswordPage() {
   const router = useRouter();
   const [token, setToken] = useState('');

  const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm<ResetForm>({
    resolver: zodResolver(schema),
    mode: 'onChange',
    defaultValues: { password: '', confirmPassword: '' },
  });

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

   useEffect(() => {
     try {
       const params = new URLSearchParams(window.location.search);
       const t = params.get('token') || '';
       setToken(t);
       if (!t) {
         setError('Invalid or missing reset token.');
       }
     } catch {
       setError('Invalid or missing reset token.');
     }
   }, []);

  const onSubmit = async (data: ResetForm) => {
    try {
      setError('');
      setSuccess('');
      const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token, new_password: data.password }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      setSuccess('Password has been reset. You can now log in.');
      reset();
      setTimeout(() => {
        router.push('/');
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset password');
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl p-8 shadow">
        <div className="w-36 h-10 bg-transparent flex items-center justify-center mx-auto pb-8">
            <Image 
                src="/assets/images/logos/chat-logo.png" 
                alt="Staicey Logo" 
                width="132"
                height="36"
                style={{height: 'auto', width: '100%'}}
            />
        </div>
        <h1 className="text-2xl font-bold mb-6 text-[#252d63]">Reset password</h1>

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

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div>
            <Input
              id="password"
              type="password"
              placeholder="New password"
              {...register('password')}
              className="bg-white/10 border-black/20 h-12 rounded-md py-4 placeholder:text-gray-500"
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-500">{errors.password.message}</p>
            )}
          </div>

          <div>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="Confirm new password"
              {...register('confirmPassword')}
              className="bg-white/10 border-black/20 h-12 rounded-md py-4 placeholder:text-gray-500"
            />
            {errors.confirmPassword && (
              <p className="mt-1 text-sm text-red-500">{errors.confirmPassword.message}</p>
            )}
          </div>

          <Button
            style={{
              backgroundImage: 'linear-gradient(135deg, #4f2f78 0%, #3e50a3 55%, #252d63 100%)'
            }}
            type="submit"
            disabled={isSubmitting || !token}
            className=" text-white hover:bg-gray-100 font-semibold py-3 px-12 rounded-full"
          >
            {isSubmitting ? 'Resetting...' : 'Reset password'}
          </Button>
        </form>
      </div>
    </div>
  );
}


