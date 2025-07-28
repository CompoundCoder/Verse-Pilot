import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ImageIcon } from 'lucide-react';
import clsx from 'clsx';

// Mock Data
const mockSlides = [
  { id: 'slide-1', title: 'Verse 1: John 3:16', type: 'verse' },
  { id: 'slide-2', title: 'Verse 2: Romans 8:28', type: 'verse' },
  { id: 'slide-3', title: 'Announcements', type: 'image' },
  { id: 'slide-4', title: 'Sermon Title', type: 'title' },
  { id: 'slide-5', title: 'Verse 3: Philippians 4:13', type: 'verse' },
  { id: 'slide-6', title: 'Worship Song 1', type: 'song' },
  { id: 'slide-7', title: 'Worship Song 2', type: 'song' },
  { id: 'slide-8', title: 'Closing Prayer', type: 'image' },
];

const SlideCard = ({ slide, isSelected, onSelect }) => {
  return (
    <motion.div
        layout
        onClick={() => onSelect(slide.id)}
        className={clsx(
            'h-full aspect-[16/9] rounded-md overflow-hidden cursor-pointer flex-shrink-0 group relative transition-all duration-150',
            isSelected ? 'ring-2 ring-accent' : 'hover:ring-2 ring-hover-color'
        )}
    >
        <div className="w-full h-full flex items-center justify-center bg-surface">
            <ImageIcon size={32} className="text-text-secondary opacity-50" />
        </div>
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
            <p className="text-white text-sm font-medium truncate">{slide.title}</p>
        </div>
    </motion.div>
  );
};

const Timeline: React.FC = () => {
  const [selectedSlideId, setSelectedSlideId] = useState<string | null>('slide-1');
  const filmstripRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = filmstripRef.current;
    if (!element) return;

    const onWheel = (e: WheelEvent) => {
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;
      e.preventDefault();
      element.scrollLeft += e.deltaY;
    };

    element.addEventListener('wheel', onWheel, { passive: false });
    return () => element.removeEventListener('wheel', onWheel);
  }, []);

  return (
    <div ref={filmstripRef} className="h-full overflow-x-auto overflow-y-hidden p-2">
        <motion.div className="flex h-full gap-3">
            <AnimatePresence>
                {mockSlides.map(slide => (
                    <SlideCard
                        key={slide.id}
                        slide={slide}
                        isSelected={selectedSlideId === slide.id}
                        onSelect={setSelectedSlideId}
                    />
                ))}
            </AnimatePresence>
        </motion.div>
    </div>
  );
};

export default Timeline; 