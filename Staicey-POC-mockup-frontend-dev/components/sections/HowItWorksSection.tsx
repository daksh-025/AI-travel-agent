'use client';

import { motion } from 'framer-motion';

export default function FeaturesSection() {

  return (
    <section id="how-it-works" className="py-24 bg-[#eee] text-white">
      <div className='flex flex-col align-center justify-center '>
        <div className='flex flex-col align-center justify-center pb-16 text-[#252d63]'>
          <div className='text-center text-4xl font-bold mx-2'>
            How does it work?
          </div>
          <div className='text-center mt-8 text-xl px-2'>
            Finding your perfect stay is at easy as having a conversation with a friend.
          </div>
        </div>
        <div className='flex flex-wrap px-4 justify-center gap-16 sm:gap-12 items-center'>
          <div className='flex bg-[#3e50a3] border-opacity-50 gap-8 rounded-2xl p-3 sm:p-8'>
            <div className='flex flex-col relative align-center justify-center'>
              <div className='absolute -top-[46px] sm:-top-[72px] left-[90px] sm:left-20 bg-[#3e50a3] w-12 h-12 text-4xl font-bold rounded-full py-[30px] px-[30px] sm:py-[40px] sm:px-[40px] flex items-center justify-center'>
                1
              </div>
              <div className='text-xl mt-2 w-60 text-center'>Tell her what you want</div>
              <div className='text-md mt-6 w-60 text-center'>Describe what you’re after in natural language - e.g. where, when, who & your budget.</div>
            </div>
          </div>
          <div className='flex bg-[#3e50a3] border-opacity-50 gap-8 rounded-2xl p-3 sm:p-8'>
            <div className='flex flex-col relative align-center justify-center'>
              <div className='absolute -top-[46px] sm:-top-[72px] left-[90px] sm:left-20 bg-[#3e50a3] w-12 h-12 text-4xl font-bold rounded-full py-[30px] px-[30px] sm:py-[40px] sm:px-[40px] flex items-center justify-center'>
                2
              </div>
              <div className='text-xl mt-2 w-60 text-center'>Staicey trawls the web</div>
              <div className='text-md mt-6 w-60 text-center'>She’ll scan the internet to find options that perfectly suit your requirements and preferences.</div>
            </div>
          </div>
          <div className='flex bg-[#3e50a3] border-opacity-50 gap-8 rounded-2xl p-3 sm:p-8'>
            <div className='flex flex-col relative align-center justify-center'>
              <div className='absolute -top-[46px] sm:-top-[72px] left-[90px] sm:left-20 bg-[#3e50a3] w-12 h-12 text-4xl font-bold rounded-full py-[30px] px-[30px] sm:py-[40px] sm:px-[40px] flex items-center justify-center'>
                3
              </div>
              <div className='text-xl mt-2 w-60 text-center'>See  recommendations</div>
              <div className='text-md mt-6 w-60 text-center'>Staicey will give you the best recommendations, saving you so much time and hassle!</div>
            </div>
          </div>
        </div>
        
        
      </div>
    </section>
  );
}