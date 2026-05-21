"use client";

type Props = {
  date: string | Date;
};

function prettyDate(d: string | Date) {
  if (!d) return "";
  
  const date = typeof d === "string" ? new Date(d) : d;
  
  // Check if the date is valid
  if (isNaN(date.getTime())) {
    return "";
  }
  
  return date
    .toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })
    .toUpperCase();
}

export default function DateSeparator({ date }: Props) {
  return (
    <div className="flex items-center gap-3 my-4">
      <div className="flex-1 h-px bg-gray-300" />
      <div className="text-xs text-gray-400 whitespace-nowrap">{prettyDate(date)}</div>
      <div className="flex-1 h-px bg-gray-300" />
    </div>
  );
}
