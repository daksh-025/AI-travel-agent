import asyncio
import random
from typing import AsyncGenerator, List
from app.chat.streaming_models import ProgressUpdate, ProgressPhase


class ProgressService:
    """Service for generating realistic progress indicators during AI processing"""
    
    # Predefined progress messages for different phases
    PROGRESS_MESSAGES = {
        ProgressPhase.STARTING: [
            "Getting started...",
            "Initializing search...",
            "Preparing your request..."
        ],
        ProgressPhase.SEARCHING_BOOKING: [
            "Searching booking.com...",
            "Checking Booking.com availability...",
            "Scanning Booking.com properties..."
        ],
        ProgressPhase.CHECKING_GOOGLE: [
            "Checking Google hotels...",
            "Searching Google Travel...",
            "Analyzing Google hotel listings..."
        ],
        ProgressPhase.ANALYZING_SITES: [
            "Analyzing 150 other accommodation sites...",
            "Comparing prices across multiple platforms...",
            "Scanning Expedia, Hotels.com, Agoda...",
            "Checking Airbnb and vacation rentals...",
            "Reviewing boutique hotel sites..."
        ],
        ProgressPhase.THINKING_PREFERENCES: [
            "Thinking about your specific preferences...",
            "Analyzing your travel style...",
            "Considering your requirements...",
            "Processing your criteria..."
        ],
        ProgressPhase.MATCHING_OPTIONS: [
            "Matching you to the best options...",
            "Ranking hotels by relevance...",
            "Finding perfect matches...",
            "Selecting top recommendations..."
        ],
        ProgressPhase.GENERATING_RESPONSE: [
            "Preparing your results...",
            "Generating personalized recommendations...",
            "Finalizing your hotel options..."
        ]
    }
    
    # Timing configuration for realistic progress
    PHASE_DURATIONS = {
        ProgressPhase.STARTING: (0.5, 1.0),
        ProgressPhase.SEARCHING_BOOKING: (1.5, 2.5),
        ProgressPhase.CHECKING_GOOGLE: (1.0, 2.0),
        ProgressPhase.ANALYZING_SITES: (2.0, 3.5),
        ProgressPhase.THINKING_PREFERENCES: (1.0, 1.5),
        ProgressPhase.MATCHING_OPTIONS: (1.5, 2.0),
        ProgressPhase.GENERATING_RESPONSE: (1.0, 1.5)
    }
    
    @classmethod
    async def generate_progress_updates(
        cls, 
        phases: List[ProgressPhase] = None,
        total_duration: float = None
    ) -> AsyncGenerator[ProgressUpdate, None]:
        """
        Generate realistic progress updates for the specified phases
        
        Args:
            phases: List of phases to progress through (default: all phases)
            total_duration: Total time to spread across all phases (default: calculated from phase durations)
            
        Yields:
            ProgressUpdate objects with realistic timing and messages
        """
        if phases is None:
            phases = [
                ProgressPhase.STARTING,
                ProgressPhase.SEARCHING_BOOKING,
                ProgressPhase.CHECKING_GOOGLE,
                ProgressPhase.ANALYZING_SITES,
                ProgressPhase.THINKING_PREFERENCES,
                ProgressPhase.MATCHING_OPTIONS,
                ProgressPhase.GENERATING_RESPONSE
            ]
        
        # Calculate total duration if not provided
        if total_duration is None:
            total_duration = sum(
                (cls.PHASE_DURATIONS.get(phase, (1.0, 2.0))[0] + 
                 cls.PHASE_DURATIONS.get(phase, (1.0, 2.0))[1]) / 2
                for phase in phases
            )
        
        # Calculate time allocation per phase
        phase_durations = []
        total_expected = sum(
            (cls.PHASE_DURATIONS.get(phase, (1.0, 2.0))[0] + 
             cls.PHASE_DURATIONS.get(phase, (1.0, 2.0))[1]) / 2
            for phase in phases
        )
        
        for phase in phases:
            min_dur, max_dur = cls.PHASE_DURATIONS.get(phase, (1.0, 2.0))
            expected_dur = (min_dur + max_dur) / 2
            allocated_dur = (expected_dur / total_expected) * total_duration
            phase_durations.append(allocated_dur)
        
        current_percentage = 0
        
        for i, phase in enumerate(phases):
            phase_duration = phase_durations[i]
            phase_start_percentage = current_percentage
            phase_end_percentage = current_percentage + (100 / len(phases))
            
            # Get random message for this phase
            messages = cls.PROGRESS_MESSAGES.get(phase, ["Processing..."])
            message = random.choice(messages)
            
            # Initial phase update
            yield ProgressUpdate(
                phase=phase,
                message=message,
                percentage=int(phase_start_percentage),
                details=f"Phase {i+1} of {len(phases)}"
            )
            
            # Simulate realistic progress within the phase
            steps = random.randint(2, 4)  # 2-4 updates per phase
            for step in range(1, steps + 1):
                step_percentage = phase_start_percentage + (
                    (phase_end_percentage - phase_start_percentage) * step / steps
                )
                
                # Add some randomness to timing
                step_delay = phase_duration / steps
                step_delay += random.uniform(-0.2, 0.3)  # Add jitter
                step_delay = max(0.1, step_delay)  # Minimum delay
                
                await asyncio.sleep(step_delay)
                
                # Occasionally change message within phase for longer phases
                if step > 1 and len(messages) > 1 and random.random() < 0.4:
                    message = random.choice(messages)
                
                yield ProgressUpdate(
                    phase=phase,
                    message=message,
                    percentage=int(step_percentage),
                    details=f"Phase {i+1} of {len(phases)}"
                )
            
            current_percentage = phase_end_percentage
        
        # Final completion update
        yield ProgressUpdate(
            phase=ProgressPhase.COMPLETE,
            message="Complete!",
            percentage=100,
            details="All phases completed"
        )
    
    @classmethod
    async def generate_hotel_search_progress(cls) -> AsyncGenerator[ProgressUpdate, None]:
        """Generate progress updates specifically for hotel searches"""
        phases = [
            ProgressPhase.STARTING,
            ProgressPhase.SEARCHING_BOOKING,
            ProgressPhase.CHECKING_GOOGLE,
            ProgressPhase.ANALYZING_SITES,
            ProgressPhase.THINKING_PREFERENCES,
            ProgressPhase.MATCHING_OPTIONS,
            ProgressPhase.GENERATING_RESPONSE
        ]
        
        async for update in cls.generate_progress_updates(phases, total_duration=8.0):
            yield update
    
    @classmethod
    async def generate_web_search_progress(cls) -> AsyncGenerator[ProgressUpdate, None]:
        """Generate progress updates specifically for web searches"""
        phases = [
            ProgressPhase.STARTING,
            ProgressPhase.ANALYZING_SITES,
            ProgressPhase.GENERATING_RESPONSE
        ]
        
        async for update in cls.generate_progress_updates(phases, total_duration=4.0):
            yield update
    
    @classmethod
    async def generate_general_chat_progress(cls) -> AsyncGenerator[ProgressUpdate, None]:
        """Generate progress updates for general chat (no tools)"""
        phases = [
            ProgressPhase.THINKING_PREFERENCES,
            ProgressPhase.GENERATING_RESPONSE
        ]
        
        async for update in cls.generate_progress_updates(phases, total_duration=2.0):
            yield update
