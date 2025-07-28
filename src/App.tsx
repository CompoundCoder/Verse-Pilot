import { useState, useCallback, useEffect } from 'react';
import React from 'react';
import clsx from 'clsx';
import Resizer from './components/ui/Resizer';
import MediaBrowserPanel from './components/MediaBrowserPanel';
import Viewer from './components/ui/Viewer';
import Timeline from './components/Timeline';
import RightPanel from './components/ui/RightPanel';

function App() {
  const [isMediaPanelExpanded, setIsMediaPanelExpanded] = useState(true);
  const [leftPanelWidth, setLeftPanelWidth] = useState(window.innerWidth * 0.25);
  const [rightPanelWidth, setRightPanelWidth] = useState(288);
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      if (isMediaPanelExpanded) {
        setLeftPanelWidth(Math.max(window.innerWidth * 0.25, 240));
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isMediaPanelExpanded]);

  const createResizeHandler = useCallback(
    (setter: React.Dispatch<React.SetStateAction<number>>) => (e: React.MouseEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsResizing(true);
      const startX = e.clientX;

      const doDrag = (moveEvent: MouseEvent) => {
        const delta = moveEvent.clientX - startX;
        if (setter === setRightPanelWidth) {
          setter((prev) => Math.max(200, Math.min(prev - delta, 500)));
        }
      };

      const stopDrag = () => {
        document.documentElement.style.cursor = '';
        window.removeEventListener('mousemove', doDrag);
        window.removeEventListener('mouseup', stopDrag);
        setIsResizing(false);
      };

      document.documentElement.style.cursor = 'col-resize';
      window.addEventListener('mousemove', doDrag);
      window.addEventListener('mouseup', stopDrag);
    },
    []
  );

  const handleCollapseToggle = (expanded: boolean) => {
    setIsMediaPanelExpanded(expanded);
    setLeftPanelWidth(expanded ? Math.max(window.innerWidth * 0.25, 240) : 96);
  };

  return (
    <div className="flex flex-col h-screen bg-bg-primary font-sans text-text-primary overflow-hidden select-none">
      <div className="flex-1 flex flex-row min-h-0 p-2 gap-2">
        {/* Left Panel */}
        <div
          className="flex-shrink-0 transition-all duration-300 ease-in-out"
          style={{ width: `${leftPanelWidth}px` }}
        >
          <MediaBrowserPanel onCollapseToggle={handleCollapseToggle} />
        </div>
        
        {/* Center Panel & Timeline */}
        <div className="flex-1 flex flex-col min-w-0 gap-2">
          <div className="flex-1 bg-bg-secondary rounded-lg p-2">
            <Viewer />
          </div>
          <div className="h-40 flex-shrink-0 bg-bg-secondary rounded-lg">
            <Timeline />
          </div>
        </div>

        {/* Right Panel */}
        <Resizer onMouseDown={createResizeHandler(setRightPanelWidth)} direction="vertical" />
        <div
          className="flex-shrink-0"
          style={{ width: `${rightPanelWidth}px` }}
        >
          <div className="h-full bg-bg-secondary rounded-lg p-2">
            <RightPanel />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 