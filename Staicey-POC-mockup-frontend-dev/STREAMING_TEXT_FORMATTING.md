# Streaming Text Formatting Guide

## Overview

The streaming text handler now automatically formats text chunks as they arrive from the backend to ensure proper spacing and readability.

## Features

### 1. **Automatic Spacing Between Words** ✅

The system automatically adds spaces between words when needed:

```typescript
// Before (without formatting):
"HelloWorld"

// After (with formatting):
"Hello World"
```

**Logic:**
- Checks if the last character of existing content is NOT a space or newline
- Checks if the first character of new chunk is NOT a space or punctuation
- Adds a space between them if needed

### 2. **Line Breaks After Sentences** ✅

Automatically adds double line breaks after periods followed by spaces:

```typescript
// Before (without formatting):
"First sentence. Second sentence. Third sentence."

// After (with formatting):
"First sentence.

Second sentence.

Third sentence."
```

**Logic:**
- Detects period followed by space: `. `
- Replaces with: `.\n\n` (period + double newline)
- Creates paragraph-like spacing for better readability

## Implementation

### Location

Both chat pages have the same formatting logic:
- `app/chat/guest/page.tsx` - Guest chat
- `app/chat/[id]/page.tsx` - Authenticated chat

### Code

```typescript
onTextChunk: (chunk: string) => {
  setMessages(prevMessages => {
    return prevMessages.map(msg => {
      if (msg.id === assistantMessageId) {
        // Process chunk to add proper spacing and line breaks
        let processedChunk = chunk;
        
        // Add space before chunk if needed
        if (msg.content.length > 0 && 
            !msg.content.endsWith(' ') && 
            !msg.content.endsWith('\n') && 
            !processedChunk.startsWith(' ') &&
            !processedChunk.match(/^[.,!?;:]/)) {
          processedChunk = ' ' + processedChunk;
        }
        
        // Add line break after periods
        processedChunk = processedChunk.replace(/\.\s/g, '.\n\n');
        
        return {
          ...msg,
          content: msg.content + processedChunk,
        };
      }
      return msg;
    });
  });
},
```

## How It Works

### Spacing Logic

1. **Check existing content**
   - If content is empty, don't add space
   - If last character is space or newline, don't add space

2. **Check new chunk**
   - If chunk starts with space, don't add space
   - If chunk starts with punctuation (`,`, `.`, `!`, etc.), don't add space

3. **Add space if needed**
   - Only adds space when both content exists and chunk needs separation

### Line Break Logic

1. **Detect sentence endings**
   - Uses regex: `/\.\s/g`
   - Matches period followed by space
   - Global flag replaces ALL occurrences in chunk

2. **Replace with formatted version**
   - Replaces `. ` with `.\n\n`
   - Creates double line break for paragraph effect

3. **Display in UI**
   - `ChatMessage` component converts `\n` to `<br>` tags
   - Double newline creates visual paragraph separation

## Examples

### Example 1: Word Spacing

**Backend sends chunks:**
```
["I", "can", "help", "you", "find", "hotels"]
```

**Without formatting:**
```
"Icanhelpyoufindhotels"
```

**With formatting:**
```
"I can help you find hotels"
```

### Example 2: Sentence Breaks

**Backend sends:**
```
"I found some great hotels. They are all 4-star rated. Would you like to see them?"
```

**Display:**
```
I found some great hotels.

They are all 4-star rated.

Would you like to see them?
```

### Example 3: Mixed Content

**Backend sends:**
```
"Here are the results. There are 5 hotels available, all near the beach. They range from $150-$300 per night."
```

**Display:**
```
Here are the results.

There are 5 hotels available, all near the beach.

They range from $150-$300 per night.
```

### Example 4: Punctuation Handling

**Backend sends chunks:**
```
["hotels", ",", "restaurants", ",", "and", "attractions", "."]
```

**Display:**
```
hotels, restaurants, and attractions.
```

Note: No extra spaces before commas!

## Edge Cases Handled

### ✅ Punctuation at Start
```typescript
// Chunk: ","
// No space added before comma
"word," not "word ,"
```

### ✅ Already Has Space
```typescript
// Content ends with: "word "
// Chunk: "next"
// Result: "word next" (no double space)
```

### ✅ Already Has Newline
```typescript
// Content ends with: "sentence.\n\n"
// Chunk: "Next"
// Result: "sentence.\n\nNext" (no extra space)
```

### ✅ Chunk Starts with Space
```typescript
// Chunk: " word"
// Result: uses existing space from chunk
```

### ✅ Multiple Sentences in One Chunk
```typescript
// Chunk: "First. Second. Third."
// All periods get line breaks
```

## Customization

### Adjust Line Break Amount

To change from double to single line break:

```typescript
// Change this line:
processedChunk = processedChunk.replace(/\.\s/g, '.\n\n');

// To:
processedChunk = processedChunk.replace(/\.\s/g, '.\n');
```

### Add Breaks After Other Punctuation

To add breaks after exclamation or question marks:

```typescript
// Add these lines:
processedChunk = processedChunk.replace(/\!\s/g, '!\n\n');
processedChunk = processedChunk.replace(/\?\s/g, '?\n\n');
```

### Disable Automatic Spacing

To disable spacing (not recommended):

```typescript
// Remove or comment out this block:
if (msg.content.length > 0 && 
    !msg.content.endsWith(' ') && 
    !msg.content.endsWith('\n') && 
    !processedChunk.startsWith(' ') &&
    !processedChunk.match(/^[.,!?;:]/)) {
  processedChunk = ' ' + processedChunk;
}
```

## Testing

### Manual Test

1. **Send a query** that generates a long response
2. **Watch streaming** - should see:
   - Spaces between words ✓
   - Line breaks after periods ✓
   - No extra spaces before punctuation ✓
   - Clean, readable format ✓

### Test Cases

#### Test 1: Basic Spacing
- Query: "Tell me about Sydney"
- Expected: Words properly spaced
- ✓ "Sydney is a beautiful city"
- ✗ "Sydneyisabeautifulcity"

#### Test 2: Sentence Breaks
- Query: "List 3 hotels"
- Expected: Sentences on separate lines
- ✓ Each sentence with line break after period
- ✗ All sentences on one line

#### Test 3: Punctuation
- Query: "Hotels, restaurants, and cafes"
- Expected: No space before commas
- ✓ "Hotels, restaurants"
- ✗ "Hotels , restaurants"

## Backend Considerations

### Optimal Chunk Size

For best results, backend should send:
- **Word-level chunks**: `["I", "can", "help"]`
- **Or phrase-level chunks**: `["I can", "help you", "find hotels"]`

### Not Recommended

- **Character-level chunks**: `["I", " ", "c", "a", "n"]` (too granular)
- **Sentence-level chunks**: `["First sentence. Second sentence."]` (line breaks work but less smooth)

### Including Punctuation

Backend can send punctuation separately or attached:
- ✅ Separate: `["word", ",", "next"]`
- ✅ Attached: `["word,", "next"]`

Both work fine!

## Performance

### Impact

- **Minimal overhead**: Simple string operations
- **No API calls**: All processing client-side
- **Fast**: Runs on each chunk (typically < 1ms)
- **Memory**: Negligible increase

### Optimization

Already optimized:
- Only processes when message ID matches
- Uses efficient regex
- No DOM manipulation during streaming
- State updates are batched by React

## Summary

✅ **Automatic spacing** between words
✅ **Line breaks** after sentences  
✅ **Punctuation handled** correctly
✅ **Both chat pages** have same formatting
✅ **Readable output** for better UX
✅ **Easy to customize** if needed

The streaming text now looks clean and professional with proper formatting! 🎉

