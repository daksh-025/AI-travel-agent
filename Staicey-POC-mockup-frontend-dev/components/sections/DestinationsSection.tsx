'use client';

import { motion } from 'framer-motion';
import { MapPin, Building, Waves, Mountain, Coffee, Wine, Trees, Star } from 'lucide-react';
import Image from 'next/image'
import Link from 'next/link';

// import SydneyIcon from '../../public/assets/images/icons/sydney.svg';
// import MelbourneIcon from '../../public/assets/images/icons/melbourne.svg';
// import BrisbanceIcon from '../../public/assets/images/icons/brisbane.svg';
// import AucklandIcon from '../../public/assets/images/icons/auckland.svg';
// import GoldCoastIcon from '../../public/assets/images/icons/gold-coast.svg';
// import PerthIcon from '../../public/assets/images/icons/perth.svg';
// import WellingtonIcon from '../../public/assets/images/icons/wellington.svg';
// import QueenstownIcon from '../../public/assets/images/icons/queenstown.svg';

export default function DestinationsSection() {


  return (
    <section id="destinations" className="py-24 bg-[#fff] text-[#521d8a]">
      <div className='flex flex-col align-center justify-center'>
        <div className='flex flex-col align-center justify-center pb-16 text-[#252d63]'>
          <div className='text-center text-4xl font-bold m-2'>
            Popular destinations
          </div>
          <div className='max-w-[600px] text-center mt-8 text-xl mx-auto px-2'>
            Discover amazing hotels in Australia and New Zealand’s most sought after destinations.
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 w-[90%] mx-auto max-w-[1200px]">
          <div className='border-[#521d8a] border border-opacity-20 gap-8 rounded-[44px] p-4 sm:p-8 max-w-[300px] mx-auto'>
            <div className='flex flex-col relative align-center justify-center '>
              <div className='bg-transparent  text-4xl font-bold rounded-full flex items-center justify-center'>
                <Image src="/assets/images/icons/sydney.png" alt="Staicey - Your AI Travel Agent" width="80" height="80"/>
              </div>
              <div className='text-xl mt-2 text-center font-bold'>Sydney</div>
              <div className='text-md mt-6 text-center'>Darling Harbour, Opera House & city excitement</div>
            </div>
          </div>
          <div className='border-[#521d8a] border border-opacity-20 gap-8 rounded-[44px] p-4 sm:p-8 max-w-[300px] mx-auto'>
            <div className='flex flex-col relative align-center justify-center'>
              <div className='bg-transparent  text-4xl font-bold rounded-full flex items-center justify-center'>
              <Image src="/assets/images/icons/melbourne.png" alt="Staicey - Your AI Travel Agent" width="80" height="80"/>
              </div>
              <div className='text-xl mt-2 text-center font-bold'>Melbourne</div>
              <div className='text-md mt-6 text-center'>Culture, coffee & cool laneways</div>
            </div>
          </div>
          <div className='border-[#521d8a] border border-opacity-20 gap-8 rounded-[44px] p-4 sm:p-8 max-w-[300px] mx-auto'>
            <div className='flex flex-col relative align-center justify-center'>
              <div className='bg-transparent  text-4xl font-bold rounded-full flex items-center justify-center'>
                <Image src="/assets/images/icons/brisbane.png" alt="Staicey - Your AI Travel Agent" width="80" height="80"/>
              </div>
              <div className='text-xl mt-2 text-center font-bold'>Brisbane</div>
              <div className='text-md mt-6 text-center'>Sunshine, entertainment & river city vibes</div>
            </div>
          </div>
          <div className='border-[#521d8a] border border-opacity-20 gap-8 rounded-[44px] p-4 sm:p-8 max-w-[300px] mx-auto'>
            <div className='flex flex-col relative align-center justify-center'>
              <div className='bg-transparent  text-4xl font-bold rounded-full flex items-center justify-center'>
                <Image src="/assets/images/icons/auckland.png" alt="Staicey - Your AI Travel Agent" width="80" height="80"/>
              </div>
              <div className='text-xl mt-2 text-center font-bold'>Auckland</div>
              <div className='text-md mt-6 text-center'>Harbours & volcanic landscapes</div>
            </div>
          </div>
          <div className='border-[#521d8a] border border-opacity-20 gap-8 rounded-[44px] p-4 sm:p-8 max-w-[300px] mx-auto'>
            <div className='flex flex-col relative align-center justify-center'>
              <div className='bg-transparent  text-4xl font-bold rounded-full flex items-center justify-center'>
                <Image src="/assets/images/icons/gold-coast.png" alt="Staicey - Your AI Travel Agent" width="80" height="80"/>
              </div>
              <div className='text-xl mt-2  text-center font-bold'>Gold Coast</div>
              <div className='text-md mt-6  text-center'>Beaches, theme parks & holiday feels</div>
            </div>
          </div>
          <div className='border-[#521d8a] border border-opacity-20 gap-8 rounded-[44px] p-4 sm:p-8 max-w-[300px] mx-auto'>
            <div className='flex flex-col relative align-center justify-center'>
              <div className='bg-transparent  text-4xl font-bold rounded-full flex items-center justify-center'>
                <Image src="/assets/images/icons/perth.png" alt="Staicey - Your AI Travel Agent" width="80" height="80"/>
              </div>
              <div className='text-xl mt-2  text-center font-bold'>Perth</div>
              <div className='text-md mt-6  text-center'>Pristine beaches and wine country</div>
            </div>
          </div>
          <div className='border-[#521d8a] border border-opacity-20 gap-8 rounded-[44px] p-4 sm:p-8 max-w-[300px] mx-auto'>
            <div className='flex flex-col relative align-center justify-center'>
              <div className='bg-transparent  text-4xl font-bold rounded-full flex items-center justify-center'>
                <Image src="/assets/images/icons/wellington.png" alt="Staicey - Your AI Travel Agent" width="80" height="80"/>
              </div>
              <div className='text-xl mt-2 text-center font-bold'>Wellington</div>
              <div className='text-md mt-6 text-center'>Creative capital and craft beer heaven</div>
            </div>
          </div>
          <div className='border-[#521d8a] border border-opacity-20 gap-8 rounded-[44px] p-4 sm:p-8 max-w-[300px] mx-auto'>
            <div className='flex flex-col relative align-center justify-center'>
              <div className='bg-transparent  text-4xl font-bold rounded-full flex items-center justify-center'>
                <Image src="/assets/images/icons/queenstown.png" alt="Staicey - Your AI Travel Agent" width="80" height="80"/>
              </div>
              <div className='text-xl mt-2 text-center font-bold'>Queenstown</div>
              <div className='text-md mt-6 text-center'>Adventure sports and alpine beauty</div>
            </div>
          </div>
        </div>

        <div style={{
            backgroundImage: 'linear-gradient(135deg, #4f2f78 0%, #3e50a3 35%, #252d63 100%)'
          }} className='flex flex-col p-6 max-w-[1400px] mx-auto w-[80%] mt-28 text-white rounded-3xl'
        >
          <div className='text-center text-[25px] sm:text-3xl md:text-4xl lg:text-5xl pt-4 md:pt-12 font-semibold'>
            Discover a better way to search for accommodation
          </div>
          <div className='text-center text-md md:text-lg lg:text-2xl text-gray-200 mt-6 mb-12'>
            Join thousands of travellers who trust Staicey to find their ideal getaway.
          </div>
          <div className='flex justify-center'>
            <Link href="/chat">
              <button className="bg-white text-[#252d63] text-md md:text-lg lg:text-2xl px-6 py-4 md:px-12 md:py-6 rounded-full font-bold">
                Chat with Staicey
              </button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}