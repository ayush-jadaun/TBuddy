"use client"
import { useState, useEffect } from 'react';
import Hyperspeed from '@/components/Hyperspeed/Hyperspeed';
import LightRays from '@/components/lightrays';
import ShinyText from '@/components/ShinyText';

const placeholderTexts = [
  "Plan your dream vacation to Paris...",
  "Discover hidden gems in Tokyo...",
  "Create an adventure in Iceland...",
  "Explore the streets of New York...",
  "Find paradise in Bali...",
  "Journey through the Swiss Alps...",
  "Experience the magic of Rome...",
  "Uncover treasures in Morocco..."
];

const TypewriterPrompt = () => {
  const [displayText, setDisplayText] = useState('');
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [userInput, setUserInput] = useState('');

  useEffect(() => {
    const currentPhrase = placeholderTexts[currentPhraseIndex];
    const typingSpeed = isDeleting ? 30 : 80;
    const pauseBeforeDelete = 2000;
    const pauseBeforeNext = 500;

    const timer = setTimeout(() => {
      if (!isDeleting && displayText === currentPhrase) {
        setTimeout(() => setIsDeleting(true), pauseBeforeDelete);
      } else if (isDeleting && displayText === '') {
        setIsDeleting(false);
        setCurrentPhraseIndex((prev) => (prev + 1) % placeholderTexts.length);
        setTimeout(() => {}, pauseBeforeNext);
      } else {
        setDisplayText(
          isDeleting
            ? currentPhrase.substring(0, displayText.length - 1)
            : currentPhrase.substring(0, displayText.length + 1)
        );
      }
    }, typingSpeed);

    return () => clearTimeout(timer);
  }, [displayText, isDeleting, currentPhraseIndex]);

  return (
    <div className="relative w-full max-w-3xl">
      <div className="relative">
        <textarea
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          className="w-full min-h-[120px] bg-black/40 backdrop-blur-md border border-zinc-600/50 rounded-2xl p-5 pr-14 text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-amber-200/50 resize-none transition-all duration-300 shadow-2xl"
          placeholder={displayText}
        />
        <div className="absolute bottom-4 right-4">
          <button className="bg-gradient-to-r from-red-700 to-red-900 hover:from-red-600 hover:to-red-700 text-white p-3 rounded-xl transition-all duration-300 shadow-lg hover:shadow-cyan-500/50 group">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-5 w-5 group-hover:translate-x-0.5 transition-transform" 
              viewBox="0 0 20 20" 
              fill="currentColor"
            >
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          </button>
        </div>
      </div>
      
      <div className="mt-4 flex gap-3 flex-wrap justify-center">
        {['Weekend Getaway', 'Family Trip', 'Solo Adventure', 'Budget Travel'].map((tag) => (
          <button
            key={tag}
            className="px-4 py-2 bg-zinc-800/50 backdrop-blur-sm border border-zinc-700/50 rounded-full text-sm text-zinc-300 hover:bg-zinc-700/50 hover:border-amber-400 transition-all duration-300"
          >
            {tag}
          </button>
        ))}
      </div>
       {/* Feature Pills */}
        <div className="mt-8 flex gap-6 text-sm text-zinc-400 mb-8 justify-center">
          <div className="flex flex-row items-center gap-2">
            <div className="w-2 h-2 bg-red-900 rounded-full animate-pulse" />
            <span>Instant Planning</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-zinc-800 rounded-full animate-pulse" />
            <span>Smart Recommendations</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-yellow-800 rounded-full animate-pulse" />
            <span>Budget Friendly</span>
          </div>
        </div>

    </div>
  );
};


const Page = () => {
  const  [tite,setTitle] = useState("Where planning is Spontaneous")
  const titles = ["Where planning is Spontaneous?","Less Googles,More Goggles","Plan less,Chill more"]

  return (
    <div className="h-screen w-screen overflow-hidden bg-black relative"> 
    <div className='fixed inset-0 h-screen w-screen'>
      <LightRays/>
      </div> 
      <div className='absolute scale-60 -left-75 -top-50 bottom-0 right-0 h-full w-full'>
          <Hyperspeed
          effectOptions={{
             colors: {
      roadColor: 0x080808,
      islandColor: 0x0a0a0a,
      background: 0x000000,
      shoulderLines: 0x131318,
      brokenLines: 0x131318,
      leftCars: [0x7d0d1b, 0xa90519, 0xff102a],
      rightCars: [0xf1eece, 0xe6e2b1, 0xdfd98a],
      sticks: 0xf1eece
    }
          }}
          />
      </div>
<div className='bg-black/60 inset-0 absolute'/>  
      {/* Content Layer */}
      <div className="relative z-10 h-full w-full flex flex-col items-center justify-between px-4 py-4">
        {/* Header */}
<div className="mt-40   mb-12 text-center">
          <h1 className="text-5xl font-light bg-gradient-to-r from-white via-zinc-300 to-zinc-700 bg-clip-text text-transparent mb-4">
            <ShinyText text={""} speed={4}/>
          </h1>
          <p className="text-zinc-400 text-lg">
            Describe your dream trip and let AI craft the perfect itinerary
          </p>
        </div>
        {/* Typewriter Prompt */}
        <TypewriterPrompt />

             </div>
    </div>
  );
};

export default Page;




