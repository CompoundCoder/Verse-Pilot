import clsx from 'clsx';
import React from 'react';

interface ResizerProps {
  onMouseDown: (event: React.MouseEvent<HTMLDivElement>) => void;
  direction: 'vertical' | 'horizontal';
}

const Resizer: React.FC<ResizerProps> = ({ onMouseDown, direction }) => (
  <div
    onMouseDown={onMouseDown}
    className={clsx(
      'flex-shrink-0 bg-transparent z-10',
      { 'w-2 cursor-col-resize': direction === 'vertical', 'h-2 cursor-row-resize': direction === 'horizontal' }
    )}
  />
);

export default Resizer; 