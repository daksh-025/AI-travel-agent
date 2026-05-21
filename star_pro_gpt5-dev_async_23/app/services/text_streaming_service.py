import asyncio
import re
from typing import AsyncGenerator, Literal
from app.chat.streaming_models import TextChunk, TextChunkEvent


class TextStreamingService:
    """Service for streaming text word-by-word like ChatGPT"""
    
    # Speed configurations (delays in milliseconds)
    SPEED_CONFIG = {
        "slow": {"word_delay": (80, 150), "punctuation_delay": (200, 400)},
        "normal": {"word_delay": (30, 80), "punctuation_delay": (100, 200)},
        "fast": {"word_delay": (10, 30), "punctuation_delay": (50, 100)}
    }
    
    @classmethod
    async def stream_text(
        cls,
        text: str,
        session_id: str,
        tab_id: str = None,
        speed: Literal["fast", "normal", "slow"] = "normal"
    ) -> AsyncGenerator[TextChunkEvent, None]:
        """
        Stream text word by word with realistic typing delays
        
        Args:
            text: The complete text to stream
            session_id: Session identifier
            tab_id: Tab identifier
            speed: Streaming speed configuration
            
        Yields:
            TextChunkEvent objects for each word/chunk
        """
        if not text or not text.strip():
            return
        
        speed_config = cls.SPEED_CONFIG.get(speed, cls.SPEED_CONFIG["normal"])
        
        # Split text into words and punctuation
        tokens = cls._tokenize_text(text)
        total_tokens = len(tokens)
        
        for i, token in enumerate(tokens):
            is_final = (i == total_tokens - 1)
            
            # Determine token type
            is_punctuation = cls._is_punctuation(token)
            is_formatting = cls._is_formatting_char(token)
            
            # Determine formatting type
            formatting_type = None
            if is_formatting:
                if token == '\n':
                    formatting_type = 'newline'
                elif token == '\t':
                    formatting_type = 'tab'
                else:
                    formatting_type = 'whitespace'
            
            # Create text chunk with formatting info
            chunk = TextChunk(
                content=token,
                is_complete_word=not (is_punctuation or is_formatting),
                is_formatting=is_formatting,
                formatting_type=formatting_type,
                delay_ms=cls._get_delay_for_token(token, speed_config)
            )
            
            # Create and yield event
            event = TextChunkEvent(
                session_id=session_id,
                tab_id=tab_id,
                chunk=chunk,
                is_final_chunk=is_final
            )
            
            yield event
            
            # Wait for the specified delay
            if not is_final:  # Don't delay after the last token
                delay_seconds = chunk.delay_ms / 1000.0 if chunk.delay_ms else 0.05
                await asyncio.sleep(delay_seconds)
    
    @classmethod
    def _tokenize_text(cls, text: str) -> list[str]:
        """
        Tokenize text into words, punctuation, and formatting characters for natural streaming
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens (words, punctuation, and formatting)
        """
        # Enhanced pattern that captures:
        # - Words (\w+)
        # - Newlines (\n)
        # - Tabs (\t) 
        # - Other whitespace (\s)
        # - Punctuation ([^\w\s])
        pattern = r'(\w+|\n|\t|[^\w\s\n\t]|\s+)'
        tokens = re.findall(pattern, text)
        
        # Process tokens while preserving formatting
        processed_tokens = []
        for token in tokens:
            if token == '\n':
                # Preserve newlines as-is for formatting
                processed_tokens.append('\n')
            elif token == '\t':
                # Preserve tabs as-is for formatting
                processed_tokens.append('\t')
            elif token.strip():  # Non-empty tokens
                if token.isspace() and token != '\n' and token != '\t':
                    # Convert multiple spaces to single space (but preserve \n and \t)
                    processed_tokens.append(" ")
                else:
                    processed_tokens.append(token)
        
        return processed_tokens
    
    @classmethod
    def _is_punctuation(cls, token: str) -> bool:
        """Check if a token is punctuation"""
        return bool(re.match(r'^[^\w\s]+$', token))
    
    @classmethod
    def _is_formatting_char(cls, token: str) -> bool:
        """Check if a token is a formatting character like newline or tab"""
        return token in ['\n', '\t']
    
    @classmethod
    def _get_delay_for_token(cls, token: str, speed_config: dict) -> int:
        """
        Get appropriate delay for a token based on its type
        
        Args:
            token: The token to get delay for
            speed_config: Speed configuration dictionary
            
        Returns:
            Delay in milliseconds
        """
        import random
        
        if cls._is_formatting_char(token):
            # Special handling for formatting characters
            if token == '\n':
                # Longer pause for newlines (paragraph breaks)
                min_delay, max_delay = speed_config["punctuation_delay"]
                return random.randint(max_delay, max_delay + 100)  # Extra pause for newlines
            elif token == '\t':
                # Medium pause for tabs
                min_delay, max_delay = speed_config["word_delay"]
                return random.randint(min_delay, max_delay)
            else:
                return speed_config["word_delay"][0]  # Default
        elif cls._is_punctuation(token):
            # Longer pause for punctuation (sentence boundaries, etc.)
            min_delay, max_delay = speed_config["punctuation_delay"]
            return random.randint(min_delay, max_delay)
        else:
            # Normal word delay
            min_delay, max_delay = speed_config["word_delay"]
            base_delay = random.randint(min_delay, max_delay)
            
            # Slightly longer delay for longer words
            if len(token) > 6:
                base_delay += random.randint(10, 20)
            
            return base_delay
    
    @classmethod
    async def stream_text_simple(
        cls,
        text: str,
        session_id: str,
        tab_id: str = None,
        speed: Literal["fast", "normal", "slow"] = "normal",
        chunk_size: int = 1
    ) -> AsyncGenerator[TextChunkEvent, None]:
        """
        Simple character-by-character or chunk-by-chunk streaming
        
        Args:
            text: Text to stream
            session_id: Session identifier
            tab_id: Tab identifier
            speed: Streaming speed
            chunk_size: Number of characters per chunk
            
        Yields:
            TextChunkEvent objects
        """
        if not text:
            return
        
        speed_config = cls.SPEED_CONFIG.get(speed, cls.SPEED_CONFIG["normal"])
        base_delay = speed_config["word_delay"][0] // 3  # Faster for character streaming
        
        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i + chunk_size]
            is_final = (i + chunk_size >= len(text))
            
            chunk = TextChunk(
                content=chunk_text,
                is_complete_word=chunk_size > 1,
                delay_ms=base_delay
            )
            
            event = TextChunkEvent(
                session_id=session_id,
                tab_id=tab_id,
                chunk=chunk,
                is_final_chunk=is_final
            )
            
            yield event
            
            if not is_final:
                await asyncio.sleep(base_delay / 1000.0)
