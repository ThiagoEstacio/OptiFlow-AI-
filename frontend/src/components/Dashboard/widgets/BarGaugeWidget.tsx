import React from 'react';
import { useLiveTagData } from '../../../hooks/useLiveTagData';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface BarGaugeWidgetProps {
  widget: Widget;
}

const BarGaugeWidget: React.FC<BarGaugeWidgetProps> = ({ widget }) => {
  const tagIds = widget.config?.tagIds || [widget.config?.tagId].filter(Boolean);
  
  // Fetch data for all tags
  const tagData = tagIds.map((tagId: string) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const data = useLiveTagData({
      tagId,
      min: widget.config?.min || 0,
      max: widget.config?.max || 100,
    });
    return { tagId, ...data };
  });

  const loading = tagData.some(d => d.loading);
  const hasError = tagData.some(d => d.error);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (hasError || tagIds.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-gray-400">
          <div className="text-4xl mb-2">▬</div>
          <p className="text-sm">Drag tags here</p>
        </div>
      </div>
    );
  }

  const min = widget.config?.min || 0;
  const max = widget.config?.max || 100;

  const getBarColor = (value: number, index: number) => {
    const colors = [
      'from-blue-500 to-blue-600',
      'from-green-500 to-green-600',
      'from-purple-500 to-purple-600',
      'from-orange-500 to-orange-600',
      'from-pink-500 to-pink-600',
    ];
    
    // Check thresholds
    const thresholds = widget.config?.thresholds || [];
    for (const threshold of thresholds) {
      if (value >= threshold.value) {
        return threshold.gradient || colors[index % colors.length];
      }
    }
    
    return colors[index % colors.length];
  };

  return (
    <div className="h-full flex flex-col justify-center p-4 space-y-4 overflow-y-auto">
      {tagData.map((data, index) => {
        const numValue = typeof data.value === 'number' ? data.value : 0;
        const percentage = ((numValue - min) / (max - min)) * 100;
        const clampedPercentage = Math.max(0, Math.min(100, percentage));
        
        return (
          <div key={data.tagId || index} className="space-y-1">
            {/* Label */}
            <div className="flex justify-between items-center text-sm">
              <span className="font-medium text-gray-700 dark:text-gray-300 truncate">
                {data.tagId || `Metric ${index + 1}`}
              </span>
              <span className="font-bold text-gray-900 dark:text-white ml-2">
                {numValue.toFixed(widget.config?.decimals || 1)}{widget.config?.unit || ''}
              </span>
            </div>
            
            {/* Bar */}
            <div className="relative h-8 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r ${getBarColor(numValue, index)} transition-all duration-500 ease-out flex items-center justify-end pr-3`}
                style={{ width: `${clampedPercentage}%` }}
              >
                {clampedPercentage > 15 && (
                  <span className="text-white text-xs font-semibold">
                    {clampedPercentage.toFixed(0)}%
                  </span>
                )}
              </div>
              
              {/* Min/Max labels */}
              {widget.config?.showMinMax && (
                <>
                  <span className="absolute left-2 top-1/2 -translate-y-1/2 text-xs text-gray-500">
                    {min}
                  </span>
                  <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500">
                    {max}
                  </span>
                </>
              )}
            </div>
          </div>
        );
      })}
      
      {/* Summary */}
      {tagData.length > 1 && widget.config?.showAverage && (
        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center text-sm font-semibold">
            <span className="text-gray-600 dark:text-gray-400">Average:</span>
            <span className="text-gray-900 dark:text-white">
              {(tagData.reduce((sum, d) => sum + (typeof d.value === 'number' ? d.value : 0), 0) / tagData.length).toFixed(1)}
              {widget.config?.unit || ''}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default BarGaugeWidget;
