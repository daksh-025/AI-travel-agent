import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Script from 'next/script';
import { UserProvider } from './context/UserContext';
import { SignInUpProvider } from './context/SignInUpContext';
import { SidebarProvider } from './context/SidebarContext';
import ErrorBoundary from '@/components/ErrorBoundary';
import SessionTimeoutWarning from '@/components/ui/SessionTimeoutWarning';
import localFont from 'next/font/local'
 
// const inter = localFont({
//   src: '../public/assets/fonts/Inter-VariableFont_opsz,wght.ttf',
// })
const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Staicey | Your AI travel expert - no more endless searching!',
  description: 'An AI-powered travel assistant who automates the currently time-heavy manual process of searching for, comparing, sorting and analysing accommodation options for travel.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Script
          id="error-suppression"
          strategy="beforeInteractive"
        >
          {`
            // Suppress async listener errors from browser extensions
            window.addEventListener('error', function(e) {
              if (e.message && e.message.includes('async response') && e.message.includes('message channel closed')) {
                e.preventDefault();
                return false;
              }

              // Suppress Link href prop type warnings in production
              if (e.message && e.message.includes('Failed prop type') && e.message.includes('href')) {
                console.warn('Link href prop type warning suppressed:', e.message);
                e.preventDefault();
                return false;
              }
            });

            // Suppress unhandled promise rejections from extensions
            window.addEventListener('unhandledrejection', function(e) {
              if (e.reason && e.reason.message && e.reason.message.includes('async response')) {
                e.preventDefault();
                return false;
              }
            });

            // Suppress console warnings for prop types in development and production
            if (typeof window !== 'undefined') {
              const originalWarn = console.warn;
              const originalError = console.error;

              console.warn = function(...args) {
                const message = args.join(' ');
                if (message.includes('Failed prop type') && message.includes('href')) {
                  return; // Suppress Link href warnings
                }
                originalWarn.apply(console, args);
              };

              console.error = function(...args) {
                const message = args.join(' ');
                if (message.includes('Failed prop type') && message.includes('href')) {
                  return; // Suppress Link href errors
                }
                originalError.apply(console, args);
              };
            }
          `}
        </Script>
        <ErrorBoundary>
          <UserProvider>
            <SignInUpProvider>
              <SidebarProvider>
                {children}
                <SessionTimeoutWarning />
              </SidebarProvider>
            </SignInUpProvider>
          </UserProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
