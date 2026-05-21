export default function TypingIndicator() {
    return (
      <div className="flex space-x-1 items-center p-2">
        <span className="animate-bounce">•</span>
        <span className="animate-bounce delay-150">•</span>
        <span className="animate-bounce delay-300">•</span>
      </div>
    );
  }
  