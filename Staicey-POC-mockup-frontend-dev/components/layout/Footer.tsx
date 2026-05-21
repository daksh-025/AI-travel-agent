'use client';

import Link from 'next/link';
import { Facebook, Twitter, Instagram, Linkedin } from 'lucide-react';
import Image from 'next/image';

export default function Footer() {
  const productLinks = [
    { label: 'How It Works', href: '#how-it-works' },
    { label: 'Features', href: '#features' },
    { label: 'Pricing', href: '/#' },
    { label: 'API', href: '/#' },
  ];

  const supportLinks = [
    { label: 'Help Centre', href: '/#' },
    { label: 'Contact Us', href: '/#' },
    { label: 'Privacy Policy', href: '/#' },
    { label: 'Terms of Use', href: '/#' },
  ];

  const companyLinks = [
    { label: 'About', href: '/#' },
    { label: 'Blog', href: '/#' },
    { label: 'Careers', href: '/#' },
    { label: 'Press', href: '/#' },
  ];

  return (
    <footer className="bg-[#252d63] text-white">
      <div className="max-w-[1400px] w-[90%] mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex justify-between flex-col md:flex-row gap-8">
          {/* Brand */}
          <div className='max-w-[700px]'>
            <div className="col-span-1 flex flex-col items-center sm:items-start">
              <Link href="/" className="flex items-center space-x-2 mb-4">
              <div className="w-132 h-10 bg-transparent flex items-center justify-center">
                <Image src="/assets/images/logos/staicey-logo-white.png" alt="Staicey Logo" width={132} height={32} />
              </div>
              </Link>
              <p className="text-gray-400 mb-6 max-w-[200px]" style={{fontSize: 14}}>
                <span className='italic'>The best & easiest</span> way to find cheap accommodation in Australia & New Zealand.
              </p>
              <div className="flex space-x-4">
                <Facebook className="w-5 h-5 text-gray-400 hover:text-white cursor-pointer transition-colors" />
                <Twitter className="w-5 h-5 text-gray-400 hover:text-white cursor-pointer transition-colors" />
                <Instagram className="w-5 h-5 text-gray-400 hover:text-white cursor-pointer transition-colors" />
                <Linkedin className="w-5 h-5 text-gray-400 hover:text-white cursor-pointer transition-colors" />
              </div>
            </div>

          </div>

          <div className="flex flex-wrap flex-grow justify-between pr-2 md:pr-12 max-w-[800px] gap-2">
            
            {/* Product */}
            <div className='text-center'>
              <h3 className="mb-4" style={{fontSize: 16}}>Product</h3>
              <ul className="space-y-2">
                {productLinks.map((link) => (
                  <li key={link.label}>
                    <Link href={link.href} className="text-gray-400 hover:text-white transition-colors">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Support */}
            <div className='text-center'>
              <h3 className="mb-4">Support</h3>
              <ul className="space-y-2">
                {supportLinks.map((link) => (
                  <li key={link.label}>
                    <Link href={link.href} className="text-gray-400 hover:text-white transition-colors">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Company */}
            <div className='text-center ml-3 sm:ml-0'>
              <h3 className="mb-4">Company</h3>
              <ul className="space-y-2">
                {companyLinks.map((link) => (
                  <li key={link.label}>
                    <Link href={link.href} className="text-gray-400 hover:text-white transition-colors">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="flex flex-col md:flex-row justify-between items-center pt-8 mt-8 border-t  border-gray-700">
          <p className="text-gray-400 text-sm" style={{fontSize: 11}}>
            Copyright © 2025 Staiz.ai & Staicey.ai. All rights reserved.
          </p>
          <div className="flex space-x-6 mt-4 md:mt-0">
            <Link href="/#" className="text-gray-400 hover:text-white text-sm transition-colors">
              Cookie Settings
            </Link>
            <Link href="/#" className="text-gray-400 hover:text-white text-sm transition-colors">
              Sitemap
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}