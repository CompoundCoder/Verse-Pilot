import React from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';

const Viewer: React.FC = () => {
  return (
    <div className="h-full w-full relative flex flex-col rounded-lg overflow-hidden">
      <TransformWrapper
        initialScale={1}
        minScale={0.25}
        maxScale={4}
        centerOnInit
        limitToBounds
      >
        {({ resetTransform, centerView }) => (
          <React.Fragment>
            <div className="absolute top-2 right-2 z-10">
              <select
                className="px-2 py-1 rounded-md bg-surface text-text-primary text-sm"
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === 'fit') {
                    resetTransform();
                  } else {
                    const scale = parseFloat(value);
                    if (centerView) centerView(scale);
                  }
                }}
                defaultValue="1"
              >
                <option value="fit">Fit</option>
                <option value="0.25">25%</option>
                <option value="0.5">50%</option>
                <option value="0.75">75%</option>
                <option value="1">100%</option>
                <option value="1.5">150%</option>
                <option value="2">200%</option>
                <option value="4">400%</option>
              </select>
            </div>
            <TransformComponent
              wrapperStyle={{ width: '100%', height: '100%' }}
              contentStyle={{ width: '100%', height: '100%' }}
            >
              <div className="w-full h-full flex items-center justify-center">
                <div className="w-full h-full aspect-[16/9] rounded-2xl overflow-hidden flex items-center justify-center">
                  <img
                    src="https://placehold.co/1920x1080/000000/FFF?text=Live+Preview"
                    alt="Slide Preview"
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>
            </TransformComponent>
          </React.Fragment>
        )}
      </TransformWrapper>
    </div>
  );
};

export default Viewer; 