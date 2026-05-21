"use client";

import { ProgressUpdate } from "@/lib/types";

interface StreamingProgressProps {
  progress: ProgressUpdate;
  isVisible: boolean;
}

const StreamingProgress: React.FC<StreamingProgressProps> = ({ progress, isVisible }) => {
  if (!isVisible) return null;

  return (
    <div className="flex items-center gap-2 p-3 bg-transparent rounded-lg max-w-[75%]">
      <span className="text-sm font-medium text-gray-700">
        {progress.message}
      </span>
      <span className="text-sm text-gray-500">
        {progress.percentage}%
      </span>
    </div>
  );
};

export default StreamingProgress;
