"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle, ChevronLeft, RotateCw, Star, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

interface QuestionPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: (answers: number[]) => void;
}

type Question = {
  id: number;
  title: string;
  description: string;
  scaleHints?: {
    one: string;
    three: string;
    five: string;
  };
};

const QUESTIONS: Question[] = [
  {
    id: 1,
    title: "Price Sensitivity",
    description:
      "I’d rather save money on accommodation so I can spend more on activities and dining.",
    scaleHints: { one: "disagree", three: "Neutral", five: "agree" },
  },
  {
    id: 2,
    title: "Comfort Priority",
    description:
      "High-quality finishes, spacious rooms, and comfort are worth paying extra for.",
    scaleHints: { one: "disagree", three: "Neutral", five: "agree" },
  },
  {
    id: 3,
    title: "Splurge Willingness",
    description:
      "I like to treat myself to indulgent accommodation, even if it costs more than alternatives.",
    scaleHints: { one: "disagree", three: "Neutral", five: "agree" },
  },
  {
    id: 4,
    title: "Location Convenience",
    description:
      "Being close to attractions, transport, or a prime spot (beach, city centre, nature) is my top priority.",
    scaleHints: { one: "disagree", three: "Neutral", five: "agree" },
  },
  {
    id: 5,
    title: "Resort-Style Inclusions",
    description:
      "I prefer accommodation with amenities like pools, gyms, spas, or kids’ clubs.",
    scaleHints: { one: "disagree", three: "Neutral", five: "agree" },
  },
  {
    id: 6,
    title: "Value of Inclusions",
    description:
      "Free breakfast, late checkout, and package deals make a big difference to me.",
    scaleHints: { one: "disagree", three: "Neutral", five: "agree" },
  },
  {
    id: 7,
    title: "On-Site Convenience",
    description:
      "I’d rather stay somewhere that has everything I need on-site, even if it’s a bit out of the way.",
    scaleHints: { one: "disagree", three: "Neutral", five: "agree" },
  },
];

function computeAxes(answers: number[]) {
  // Ensure length 7 with defaults
  const a = Array.from({ length: 7 }, (_, i) => answers[i] ?? 3);

  // X Score (Budget vs Luxury): Average Q1–Q3, rescale to 0–10 (multiply by 2)
  // Q1: 1=Budget, 5=Luxury (inverted for Q1)
  // Q2: 1=Luxury, 5=Budget (inverted for Q2) 
  // Q3: 1=Luxury, 5=Budget (inverted for Q3)
  const xScore = ((6 - a[0]) + a[1] + a[2]) / 3 * 2;

  // Y Score (Location vs Amenities): Average Q4–Q7, rescale to 0–10 (multiply by 2)
  // Q4: 1=Location, 5=Amenities (inverted for Q4)
  // Q5-7: 1=Amenities, 5=Location (inverted for Q5-7)
  const yScore = ((6 - a[3]) + (6 - a[4]) + (6 - a[5]) + (6 - a[6])) / 4 * 2;

  return { xScore, yScore };
}

function getResultBlurb(answers: number[]) {
  const { xScore, yScore } = computeAxes(answers);

  // Mapping thresholds
  const isBudget = xScore < 4;
  const isLuxury = xScore > 6;
  const isLocation = yScore < 4;
  const isAmenities = yScore > 6;
  const isMidX = xScore >= 4 && xScore <= 6;
  const isMidY = yScore >= 4 && yScore <= 6;

  // Both mid → Balanced Explorer
  if (isMidX && isMidY) {
    return {
      title: "The Balanced Explorer",
      body: "You're adaptable, flexible, and game for almost anything. Sometimes you're in the mood for a simple guesthouse, other times you'll go all-in for a luxe suite. What matters most to you is the experience itself — location, amenities, budget, and luxury are all negotiable depending on the trip. Travelling with you is easy because you don't sweat the small stuff. You're open-minded, curious, and able to find joy in nearly any situation. To you, it's not about chasing perfection — it's about making memories and embracing the adventure, wherever it leads.",
    };
  }

  // Corner personalities
  if (isBudget && isLocation) {
    return {
      title: "The Deal Hunter",
      body: "You're sharp-eyed, strategic, and always one step ahead when it comes to sniffing out the best bargains. For you, travel is about location, location, location — being right in the thick of things matters far more than thread counts or luxury touches. You thrive on finding that hidden gem hotel that costs half as much but puts you within walking distance of everything you want to see. Your friends probably joke that you should moonlight as a travel agent, because you've mastered the art of doing more with less. You're not afraid of a little hustle, and you actually enjoy the hunt itself. For you, saving money isn't just practical — it's part of the fun, because every dollar saved means another adventure you can squeeze in later.",
    };
  }

  if (isLuxury && isLocation) {
    return {
      title: "The Luxe Locator",
      body: "For you, the place is everything. Whether it's a beachfront villa with the sound of waves, a mountaintop lodge with sweeping views, or a penthouse in the city's heart, you don't just book a hotel — you claim your spot in the world. You see travel as an investment in experiences that are truly unforgettable. Your friends and family probably ask you where to stay, because you've got a knack for finding that perfect location. You're unapologetic about choosing quality over compromise, because you know memories are shaped as much by setting as by activity. When you travel, it's less about ticking boxes and more about fully immersing in the vibe of the place.",
    };
  }

  if (isBudget && isAmenities) {
    return {
      title: "The Value Packager",
      body: "You're the deal detective who loves finding the most perks for the least spend. Free breakfast? Yes, please. Resort credits? Even better. You're practical and efficient, and you see amenities as more than extras — they're part of your core travel strategy. You take pride in maximising value, and you're the kind of traveller who gets genuine satisfaction from knowing you got more than what you paid for. For you, travel planning is a bit of a game: stacking deals, upgrades, and inclusions to create a trip that feels indulgent without breaking the bank.",
    };
  }

  if (isLuxury && isAmenities) {
    return {
      title: "The Indulgent Escapist",
      body: "Travel, for you, is all about being pampered. You want to arrive, put your bags down, and melt straight into relaxation mode. Spas, all-inclusive resorts, private villas, and personalised service aren't extras to you — they're the whole point. Your philosophy is simple: life is busy enough, so holidays should be extraordinary. You're unapologetically indulgent and you know how to enjoy every second of it. Whether it's sipping champagne by the pool or booking the suite with the private plunge pool, you're here for the good life — and why not? You've earned it.",
    };
  }

  // Mid-zone personalities
  if (isMidX && isLocation) {
    return {
      title: "The Chic Roamer",
      body: "Stylish, selective, and curious — you love the idea of staying somewhere that feels unique and photo-worthy. Boutique hotels, sleek Airbnbs, or design-forward stays call to you, as long as they're in a spot that lets you explore easily. You're not extreme about luxury, but you do like things to feel a little elevated. Travel for you is about balance: a bit of comfort, a touch of flair, and the flexibility to wander without being boxed into a rigid plan. You like places that feel you, not cookie-cutter — and that means your trips always have a personal stamp of style.",
    };
    
  }

  if (isMidX && isAmenities) {
    return {
      title: "The Practical Planner",
      body: "Reliable, organised, and thoughtful — you plan trips with an eye for comfort and convenience, while still keeping the budget in check. You're not out to win the cheapest trip ever award, but you're savvy enough to know where the value lies. A comfortable room, handy facilities, and smart inclusions are what make a trip feel worthwhile to you. People love travelling with you because you think ahead. You've probably compared options, checked reviews, and made sure everyone has what they need before you even pack your bags. You're steady, prepared, and always looking for that balance between cost and quality.",
    };
  }

  if (isBudget && isMidY) {
    return {
        title: "The Savvy Explorer",
        body: "You like to keep things smart and balanced — you're not chasing rock-bottom prices, but you're also not about to splash out without a good reason. Travel for you is about finding those sweet spots: well-located stays that give you comfort, convenience, and style without tipping into excess. People admire how you make clever choices that maximise experiences. You're strategic but never stingy, happy to spend a little more if it buys time, ease, or a better vibe. You're the traveller who knows when to save, when to splurge, and how to turn even a mid-range booking into a standout stay.",
      };
  }

  if (isLuxury && isMidY) {
    return {
      title: "The Comfort Seeker",
      body: "You value relaxation and convenience, but you don't need to go full red-carpet. A cosy, well-run resort with a great pool, comfy beds, and good service is exactly your style. You're the kind of traveller who wants to come home from a trip feeling rested, not exhausted. You like having nice things, but your focus is more on feeling at ease than being flashy. People love travelling with you because you prioritise comfort and happiness — making sure everyone has what they need without overcomplicating things.",
    };
  }

  // Fallback
  return {
    title: "Your Travel Personality",
    body: `Your travel style coordinates: X=${xScore.toFixed(1)} (Budget-Luxury), Y=${yScore.toFixed(1)} (Location-Amenities)`,
  };
}

export default function QuestionPopup({ isOpen, onClose, onComplete }: QuestionPopupProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    // Reset state when opened
    setCurrentIndex(0);
    setAnswers([]);
    setIsComplete(false);
  }, [isOpen]);

  const progressValue = useMemo(() => {
    const answered = Math.min(answers.length, QUESTIONS.length);
    return Math.round((answered / QUESTIONS.length) * 100);
  }, [answers.length]);

  const handleSelect = useCallback(
    (value: number) => {
      setAnswers((prev) => {
        const next = [...prev];
        next[currentIndex] = value;
        return next;
      });

      const isLast = currentIndex >= QUESTIONS.length - 1;
      if (isLast) {
        setTimeout(() => {
          setIsComplete(true);
          onComplete?.((() => {
            const arr = Array.from({ length: QUESTIONS.length }, (_, i) => (i === currentIndex ? value : answers[i] ?? 3));
            return arr;
          }) as unknown as number[]);
        }, 120);
      } else {
        setTimeout(() => setCurrentIndex((i) => i + 1), 120);
      }
    },
    [currentIndex, onComplete, answers]
  );

  const restart = useCallback(() => {
    setAnswers([]);
    setCurrentIndex(0);
    setIsComplete(false);
  }, []);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-[#eee] rounded-[12px] w-full max-w-2xl max-h-[95vh] overflow-y-auto px-4 sm:px-8 lg:px-20 py-4">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="relative flex items-center justify-between px-0 py-2 sm:py-4 border-b">
            <div className="flex items-center gap-2">
              <h2 className="text-sm sm:text-lg font-bold text-[#252d63]">Your Travel Personality</h2>
            </div>
            
            <Button className="absolute -left-6 lg:-left-16 -top-4 lg:-top-1" variant="link" size="sm" onClick={onClose}>
              <X size={20} strokeWidth={1} className="hover:text-[#111] text-[#999] sm:w-7 sm:h-7" />
            </Button>
          </div>
          {
            !isComplete && (
                <div className="space-y-2">
                    <div className="text-xs sm:text-sm text-gray-600 pt-2 sm:pt-4"><i>Let's discover your unique travel personality!</i> The more I learn about you, the better I will get at finding the perfect travel deals.
                    </div>
                    <div className="text-xs sm:text-sm font-semibold text-gray-800 pt-1 sm:pt-2 pb-1">
                        Answer these questions based on what is usually important to you when booking accommodation.
                    </div>
                </div>
            )
          }

          {/* Body */}
          <div className="mx-0 my-2 sm:my-3 px-2 sm:px-6 py-4 sm:py-6 flex items-center bg-white rounded-lg">
            {!isComplete ? (
              <div className="space-y-4 sm:space-y-6 px-2 sm:px-6 w-full">
                <div className="space-y-2">
                  <div className="text-sm sm:text-base font-medium text-center">{QUESTIONS[currentIndex].description}</div>
                </div>

                <div className="flex flex-col gap-3">
                  <div className="grid grid-cols-5 gap-2 sm:gap-3">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <Button
                        key={n}
                        variant={answers[currentIndex] === n ? "default" : "outline"}
                        className="h-8 sm:h-10 text-xs sm:text-sm rounded-lg"
                        onClick={(e) => {handleSelect(n); e.currentTarget.blur(); }}
                      >
                        {n}
                      </Button>
                    ))}
                  </div>
                  {QUESTIONS[currentIndex].scaleHints && (
                    <div className="flex items-center justify-between text-[9px] sm:text-xs text-gray-500 uppercase px-1">
                      <span className="text-center">{QUESTIONS[currentIndex].scaleHints!.one}</span>
                      <span className="text-center">{QUESTIONS[currentIndex].scaleHints!.three}</span>
                      <span className="text-center">{QUESTIONS[currentIndex].scaleHints!.five}</span>
                    </div>
                  )}
                </div>
              </div>
              ) : (
                <div className="">
                  {(() => {
                    const { title, body } = getResultBlurb(answers);
                    const { xScore, yScore } = computeAxes(answers);
                    return (
                      <>
                        <div>
                          <div className="text-lg sm:text-2xl font-bold text-center text-blue-900">{title}</div>
                        </div>
                        
                        {/* Personality Grid Chart */}
                        <div className="mt-0 mb-4 sm:mt-1 sm:mb-6 md:mt-3 md:mb-8">
                          <div className="relative mx-auto w-64 h-64 sm:w-80 sm:h-80">
                            {/* Axis labels */}
                            <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2 text-[7px] sm:text-[9px] w-64 sm:w-80 text-[#4f2f78] uppercase">
                              {`Budget/Value Driven ←————————→   Luxury/Quality Driven`}
                            </div>
                            <div className="absolute top-1/2 -left-2 transform -translate-y-1/2 -rotate-90 text-[7px] sm:text-[9px] h-64 sm:h-80 text-[#4f2f78] uppercase">
                              Location/Convenience Focus ←→ Facilities/Amenities Focus
                            </div>
                            <div className="absolute inset-0 grid grid-cols-10 grid-rows-10">
                              {/* Generate 100 cells with different colors based on position */}
                              {Array.from({ length: 100 }, (_, i) => {
                                const row = Math.floor(i / 10);
                                const col = i % 10;
                                
                                // Determine color based on position - 9 different personality areas
                                let bgColor = '';
                                if (row < 5 && col < 5) {
                                    // Bottom-left quadrant (Budget + Location)
                                    bgColor = 'bg-[#d9dced]';
                                } else if (row < 5 && col >= 5) {
                                    // Bottom-right quadrant (Luxury + Location)
                                    bgColor = 'bg-[#fef2dc]';
                                } else if (row >= 5 && col < 5) {
                                    // Top-left quadrant (Budget + Amenities)
                                    bgColor = 'bg-[#f3d6e8]';
                                } else {
                                    // Top-right quadrant (Luxury + Amenities)
                                    bgColor = 'bg-[#dcd5e4]';
                                }

                                if((row < 3 || row > 6) && (col > 6 || col < 3)){
                                    bgColor += ' ';
                                }
                                else if((row < 6 && row > 3)  && (col < 6 && col > 3)) {
                                    bgColor += ' opacity-30';
                                }
                                else{
                                    bgColor += ' opacity-60';
                                }
                                
                                return (
                                  <div key={i} className={`${bgColor}  border-gray-100`}></div>
                                );
                              })}
                            </div>
                            
                            {/* User's position */}
                            <div 
                              className="absolute w-4 h-4 bg-transparent rounded-full  transform -translate-x-2 -translate-y-2"
                              style={{
                                left: `${((xScore )/ 10) * 100}%`,
                                top: `${100 - ((yScore) / 10) * 100}%`
                              }}
                            >
                              <Star size={18} fill="#272d64" color="#272d64" className="transform -translate-x-[2px] -translate-y-[2px]" />
                              <div className="absolute top-5 left-1/2 min-w-[80px] transform -translate-x-1/2 text-xs font-bold text-[#272d64]">YOUR SCORE</div>
                            </div>
                            
                              {/* Personality type positions (approximate) */}
                              <div className="relative text-[7px] sm:text-[9px] text-gray-500 h-64 w-64 sm:h-80 sm:w-80">
                                {/* Deal Hunter - Bottom Left */}
                                <div className="absolute text-[#c74c98]" style={{ left: '15%', top: '85%', transform: 'translate(-50%, -50%)' }}>Deal Hunter</div>
                                {/* Savvy Explorer - Mid Left */}
                                <div className="absolute text-[#c74c98]" style={{ left: '35%', top: '65%', transform: 'translate(-50%, -50%)' }}>Savvy Explorer</div>
                                {/* Value Packager - Top Left */}
                                <div className="absolute text-[#4656ad]" style={{ left: '15%', top: '15%', transform: 'translate(-50%, -50%)' }}>Value Packager</div>
                                {/* Practical Planner - Mid Top Left */}
                                <div className="absolute text-[#4656ad]" style={{ left: '35%', top: '35%', transform: 'translate(-50%, -50%)' }}>Practical Planner</div>
                                
                                {/* Luxe Locator - Bottom Right */}
                                <div className="absolute text-[#4f2f78]" style={{ left: '75%', top: '85%', transform: 'translateY(-50%)' }}>Luxe Locator</div>
                                {/* Chic Roamer - Mid Right */}
                                <div className="absolute text-[#4f2f78]" style={{ left: '65%', top: '65%', transform: 'translate(-50%, -50%)' }}>Chic Roamer</div>
                                {/* Indulgent Escapist - Top Right */}
                                <div className="absolute text-[#e7ad40]" style={{ left: '73%', top: '15%', transform: 'translateY(-50%)' }}>Indulgent Escapist</div>
                                {/* Comfort Seeker - Mid Top Right */}
                                <div className="absolute text-[#e7ad40]" style={{ left: '65%', top: '35%', transform: 'translate(-50%, -50%)' }}>Comfort Seeker</div>
                                
                                {/* Balanced Explorer - Center */}
                                <div className="absolute w-8 sm:w-10 text-center text-[#2a3677]" style={{ left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}>Balanced Explorer</div>
                              </div>
                          </div>
                          
                        </div>
                        
                        <p className="text-gray-700 leading-relaxed px-1 sm:px-2 text-xs sm:text-sm">{body}</p>
                      </>
                    );
                  })()}
                </div>
              )}
          </div>

          {
            !isComplete ?
              (
                <div className="flex items-center justify-center mb-4 sm:mb-6">
                    <Button variant="ghost" className={`h-5 p-2 text-[10px] sm:text-[12px] text-[#4f2f78] ${currentIndex > 0 ? 'visible' : 'invisible'}`}>
                        <ChevronLeft size={14} color="#4f2f78" /> BACK
                    </Button>
                    {/* Footer Progress */}
                    <div className="flex-1 px-2">
                        <Progress value={isComplete ? 100 : progressValue} className="h-1.5 sm:h-2" />
                    </div>
                    <Button variant="ghost" className="invisible h-5 p-2 text-[10px] sm:text-[12px]">
                        ABACK
                    </Button>
                </div>
              ) :
              (
                <div className="flex flex-col sm:flex-row items-center justify-between gap-2 sm:gap-0">
                    <div className="flex items-center text-xs sm:text-sm text-[#4f2f78]">
                        <RotateCw size={12} className="mr-1" />
                        <p>Not quite right?</p>
                        <Button onClick={restart} variant="ghost" className="p-1 ml-1 underline hover:bg-transparent text-xs">Try quiz again</Button>
                    </div>
                    <Button onClick={onClose} className="rounded-full px-4 py-2 sm:p-6 font-bold bg-[#272d64] text-xs sm:text-sm"><CheckCircle size={14} className="mr-1 sm:mr-2" /> Yep - thats me, alright!</Button>
                </div>
              )
          }
            
        </div>
      </div>
    </div>
  );
}


