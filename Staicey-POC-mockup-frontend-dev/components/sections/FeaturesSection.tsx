'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';

export default function FeaturesSection() {
  const features = [
    {
      title: 'Lightning Fast',
      description: 'Get hotel options in seconds, not hours. Staicey searches and compares options instantly.'
    },
    {
      title: 'Personalised',
      description: 'She learns your preferences and finds options to suit options that suit you perfectly!'
    },
    {
      title: 'Verified Deals',
      description: 'Real-time pricing & availability checks provide you get accurate information.'
    }
  ];

  return (
    <section id="features" className="py-24 bg-[#252d63] text-white">
      <div className='flex flex-col align-center justify-center '>
        <div className='flex flex-col align-center justify-center pb-16'>
          <div className='text-center text-4xl font-bold m-2'>
            Why choose Staicey?
          </div>
          <div className='text-center px-2 mt-8 mx-auto max-w-[550px]' style={{fontSize: 18}}>
           Staicey makes finding the perfect getaway effortless with clever AI-powered technology and ultra-personalised recommendations.
          </div>
        </div>
        <div className='flex flex-wrap justify-center gap-12 items-center px-4'>
          <div className='flex border border-[#3e50a3] border-opacity-50 gap-8 rounded-2xl p-8'>
            <div className='flex flex-col relative text-center'>
              <div className='absolute -top-16 left-[42px]  bg-[#252d63] px-2'>
                <Image src="/assets/images/icons/lightning-fast.png" alt="Staicey - Your AI Travel Agent" width="70" height="70"/>
              </div>
              <div className='text-xl'>Lightning Fast</div>
              <div className='text-xs mt-6 w-44'>Get hotel options in seconds, <br/>not hours. Staicey searches & <br/>compares options instantly.</div>
            </div>
          </div>
          <div className='flex border border-[#3e50a3] border-opacity-50 gap-8 rounded-2xl p-8'>
            <div className='flex flex-col relative text-center'>
              <div className='absolute -top-16 left-[42px]  bg-[#252d63] px-2'>
                <Image src="/assets/images/icons/personalised.png" alt="Staicey - Your AI Travel Agent" width="70" height="70"/>
              </div>
              <div className='text-xl'>Personalised</div>
              <div className='text-xs mt-6 w-44'>She learns your preferences over time to find options that suit you perfectly!</div>
            </div>
          </div>
          <div className='flex border border-[#3e50a3] border-opacity-50 gap-8 rounded-2xl p-8'>
            <div className='flex flex-col relative text-center'>
              <div className='absolute -top-16 left-[42px]  bg-[#252d63] px-2'>
                <Image src="/assets/images/icons/verified-deals.png" alt="Staicey - Your AI Travel Agent" width="70" height="70"/>
              </div>
              <div className='text-xl'>Verified Deals</div>
              <div className='text-xs mt-6 w-44'>Real-time pricing & availability checks ensure you get accurate information.</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}