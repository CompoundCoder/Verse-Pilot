import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { ImageIcon } from 'lucide-react';

interface MediaCardProps {
  title: string;
  thumbnailUrl: string | null;
  isSelected: boolean;
  onClick: () => void;
}

const MediaCard: React.FC<MediaCardProps> = ({ title, thumbnailUrl, isSelected, onClick }) => {
  const cardVariants = {
    hidden: { opacity: 0, scale: 0.95 },
    visible: { opacity: 1, scale: 1 },
  };

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      exit="hidden"
      layout
      onClick={onClick}
      className={clsx(
        'aspect-[16/9] rounded-md overflow-hidden cursor-pointer group relative transition-all duration-150',
        isSelected ? 'ring-2 ring-accent' : 'hover:ring-2 hover:ring-hover-color'
      )}
    >
      {thumbnailUrl ? (
        <img
          src={thumbnailUrl}
          alt={title}
          className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-300"
          loading="lazy"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-surface">
          <ImageIcon size={32} className="text-text-secondary opacity-50" />
        </div>
      )}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
        <p className="text-white text-sm font-medium truncate">{title}</p>
      </div>
    </motion.div>
  );
};

export default MediaCard; 