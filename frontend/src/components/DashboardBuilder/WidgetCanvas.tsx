/**
 * Widget Canvas - Drop Target
 * Main area where widgets are displayed and can receive tag drops
 */

import React from 'react';
import { useDrop } from 'react-dnd';
import { WidgetComponent } from './WidgetComponent';
import type { Widget } from '../../pages/DashboardBuilderPage';

interface WidgetCanvasProps {
  widgets: Widget[];
  selectedWidget: string | null;
  onSelectWidget: (id: string | null) => void;
  onUpdateWidget: (id: string, updates: Partial<Widget>) => void;
  onDeleteWidget: (id: string) => void;
  onBindTag: (widgetId: string, tagId: string) => void;
}

export const WidgetCanvas: React.FC<WidgetCanvasProps> = ({
  widgets,
  selectedWidget,
  onSelectWidget,
  onUpdateWidget,
  onDeleteWidget,
  onBindTag,
}) => {
  const [{ isOver }, drop] = useDrop(() => ({
    accept: 'TAG',
    drop: (item: any, monitor) => {
      // This handles dropping tags onto the canvas (not on widgets)
      // We could create a new widget here automatically
      return { dropped: true };
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
    }),
  }));

  return (
    <div
      ref={drop}
      className={`
        flex-1 overflow-auto relative bg-gray-100
        ${isOver ? 'bg-blue-50' : ''}
      `}
      onClick={() => onSelectWidget(null)}
    >
      {/* Grid Pattern (optional) */}
      <div
        className="absolute inset-0 opacity-10 pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(circle, #000 1px, transparent 1px)',
          backgroundSize: '20px 20px',
        }}
      />

      {/* Widgets */}
      {widgets.length === 0 ? (
        <div className="absolute inset-0 flex items-center justify-center text-gray-400">
          <div className="text-center">
            <p className="text-lg font-medium mb-2">Empty Dashboard</p>
            <p className="text-sm">Add widgets using the toolbar above</p>
            <p className="text-sm mt-1">Then drag tags onto them to display data</p>
          </div>
        </div>
      ) : (
        widgets.map((widget) => (
          <WidgetComponent
            key={widget.id}
            widget={widget}
            isSelected={selectedWidget === widget.id}
            onSelect={() => onSelectWidget(widget.id)}
            onUpdate={(updates) => onUpdateWidget(widget.id, updates)}
            onDelete={() => onDeleteWidget(widget.id)}
            onBindTag={(tagId) => onBindTag(widget.id, tagId)}
          />
        ))
      )}
    </div>
  );
};
