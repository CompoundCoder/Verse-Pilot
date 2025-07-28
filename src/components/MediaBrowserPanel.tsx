import React, { useState, useMemo } from 'react';
import clsx from 'clsx';
import MediaCard from './ui/MediaCard';
import { BookText, Music, Image as ImageIcon } from 'lucide-react';
import SearchBar from './ui/SearchBar';

type Tab = 'Bible' | 'Songs' | 'Media';

interface TabConfig {
  id: Tab;
  label: string;
  icon: React.ElementType;
}

const tabsConfig: TabConfig[] = [
    { id: 'Bible', label: 'Bible', icon: BookText },
    { id: 'Songs', label: 'Songs', icon: Music },
    { id: 'Media', label: 'Media', icon: ImageIcon },
];

// Mock Data
const mockData = {
  Bible: [
    { id: 'v1', title: 'John 3:16', thumbnailUrl: 'https://picsum.photos/id/101/320/180' },
    { id: 'v2', title: 'Romans 8:28', thumbnailUrl: 'https://picsum.photos/id/102/320/180' },
    { id: 'v3', title: 'Philippians 4:13', thumbnailUrl: 'https://picsum.photos/id/103/320/180' },
  ],
  Songs: [
    { id: 's1', title: 'Amazing Grace', thumbnailUrl: 'https://picsum.photos/id/201/320/180' },
    { id: 's2', title: 'How Great Thou Art', thumbnailUrl: 'https://picsum.photos/id/202/320/180' },
  ],
  Media: [
    { id: 'm1', title: 'Sermon Background 1', thumbnailUrl: 'https://picsum.photos/id/301/320/180' },
    { id: 'm2', title: 'Welcome Video', thumbnailUrl: 'https://picsum.photos/id/302/320/180' },
    { id: 'm3', title: 'Offering Graphic', thumbnailUrl: 'https://picsum.photos/id/303/320/180' },
    { id: 'm4', title: 'Cross Image', thumbnailUrl: 'https://picsum.photos/id/304/320/180' },
  ],
};

interface MediaBrowserPanelProps {
  onCollapseToggle: (expanded: boolean) => void;
}

const MediaBrowserPanel: React.FC<MediaBrowserPanelProps> = ({ onCollapseToggle }) => {
  const [activeTab, setActiveTab] = useState<Tab>('Bible');
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isContentVisible, setIsContentVisible] = useState(true);

  const handleTabChange = (tab: Tab) => {
    if (tab === activeTab) {
      const newVisibility = !isContentVisible;
      setIsContentVisible(newVisibility);
      onCollapseToggle(newVisibility);
    } else {
      setActiveTab(tab);
      setSearchQuery('');
      setSelectedItemId(null);
      setIsContentVisible(true);
      onCollapseToggle(true);
    }
  };

  const filteredItems = useMemo(() => {
    const items = mockData[activeTab];
    if (!searchQuery) return items;
    return items.filter(item =>
      item.title.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [activeTab, searchQuery]);

  return (
    <div className="h-full bg-bg-secondary rounded-lg flex flex-row overflow-hidden">
      {/* Vertical Tab Navigation */}
      <div className="w-24 flex-shrink-0 p-2 border-r border-border-color">
        <div className="flex flex-col items-center justify-start gap-2 h-full">
          {tabsConfig.map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={clsx(
                'flex flex-col items-center justify-center p-2 rounded-lg w-full transition-colors aspect-square',
                activeTab === tab.id && isContentVisible
                  ? 'bg-accent text-button-text'
                  : 'text-text-secondary hover:bg-surface'
              )}
            >
              <tab.icon size={24} />
              <span className="text-xs mt-1 font-semibold">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Media Grid */}
      {isContentVisible && (
        <div className="flex-1 flex flex-col p-2 overflow-hidden min-w-0">
          <div className="flex-shrink-0 mb-2">
              <SearchBar 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={`Search ${activeTab}...`}
              />
          </div>
          <div className="flex-1 overflow-y-auto">
            <div className="grid grid-cols-2 gap-2">
                {filteredItems.map(item => (
                <MediaCard
                    key={item.id}
                    title={item.title}
                    thumbnailUrl={item.thumbnailUrl}
                    isSelected={selectedItemId === item.id}
                    onClick={() => setSelectedItemId(item.id)}
                />
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MediaBrowserPanel; 