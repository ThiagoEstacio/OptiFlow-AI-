/**
 * Chart Annotation Component
 * ==========================
 *
 * Permite adicionar anotações em gráficos para destacar eventos,
 * anomalias ou pontos importantes nos dados.
 */
import React, { useState, useCallback } from 'react';
import { MessageSquare, X, Edit2, Trash2, Check, AlertTriangle, Info, Flag } from 'lucide-react';

export interface Annotation {
  id: string;
  x: number | string;
  y?: number;
  text: string;
  type: 'note' | 'alert' | 'info' | 'milestone';
  author?: string;
  createdAt: Date;
  color?: string;
}

interface ChartAnnotationProps {
  annotations: Annotation[];
  onAdd?: (annotation: Omit<Annotation, 'id' | 'createdAt'>) => void;
  onEdit?: (id: string, text: string) => void;
  onDelete?: (id: string) => void;
  readOnly?: boolean;
  className?: string;
}

// Annotation marker component (to be placed on chart)
interface AnnotationMarkerProps {
  annotation: Annotation;
  position: { x: number; y: number };
  onEdit?: () => void;
  onDelete?: () => void;
  readOnly?: boolean;
}

export const AnnotationMarker: React.FC<AnnotationMarkerProps> = ({
  annotation,
  position,
  onEdit,
  onDelete,
  readOnly = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const typeStyles = {
    note: { bg: 'bg-blue-500', icon: MessageSquare },
    alert: { bg: 'bg-red-500', icon: AlertTriangle },
    info: { bg: 'bg-cyan-500', icon: Info },
    milestone: { bg: 'bg-purple-500', icon: Flag },
  };

  const style = typeStyles[annotation.type] || typeStyles.note;
  const Icon = style.icon;

  return (
    <div
      className="absolute z-10"
      style={{ left: position.x, top: position.y, transform: 'translate(-50%, -100%)' }}
    >
      {/* Marker */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`${style.bg} text-white p-1.5 rounded-full shadow-lg hover:scale-110 transition-transform`}
        aria-label={`Anotação: ${annotation.text}`}
      >
        <Icon className="w-3 h-3" />
      </button>

      {/* Connector line */}
      <div className={`absolute left-1/2 top-full w-0.5 h-3 ${style.bg} -translate-x-1/2`} />

      {/* Expanded tooltip */}
      {isExpanded && (
        <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-64 bg-white rounded-lg shadow-xl border border-slate-200 overflow-hidden">
          {/* Header */}
          <div className={`${style.bg} px-3 py-2 flex items-center justify-between`}>
            <div className="flex items-center gap-2 text-white">
              <Icon className="w-4 h-4" />
              <span className="text-xs font-medium uppercase">
                {annotation.type === 'note' ? 'Nota' :
                 annotation.type === 'alert' ? 'Alerta' :
                 annotation.type === 'info' ? 'Informação' : 'Marco'}
              </span>
            </div>
            <button
              onClick={() => setIsExpanded(false)}
              className="text-white/80 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Content */}
          <div className="p-3">
            <p className="text-sm text-slate-700">{annotation.text}</p>
            {annotation.author && (
              <p className="text-xs text-slate-400 mt-2">
                Por {annotation.author}
              </p>
            )}
            <p className="text-xs text-slate-400">
              {annotation.createdAt.toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </div>

          {/* Actions */}
          {!readOnly && (onEdit || onDelete) && (
            <div className="flex border-t border-slate-100">
              {onEdit && (
                <button
                  onClick={onEdit}
                  className="flex-1 flex items-center justify-center gap-1 py-2 text-xs text-slate-600 hover:bg-slate-50"
                >
                  <Edit2 className="w-3 h-3" /> Editar
                </button>
              )}
              {onDelete && (
                <button
                  onClick={onDelete}
                  className="flex-1 flex items-center justify-center gap-1 py-2 text-xs text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="w-3 h-3" /> Excluir
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Add annotation form
interface AddAnnotationFormProps {
  onSubmit: (annotation: Omit<Annotation, 'id' | 'createdAt'>) => void;
  onCancel: () => void;
  defaultX?: number | string;
  defaultY?: number;
}

export const AddAnnotationForm: React.FC<AddAnnotationFormProps> = ({
  onSubmit,
  onCancel,
  defaultX,
  defaultY,
}) => {
  const [text, setText] = useState('');
  const [type, setType] = useState<Annotation['type']>('note');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    onSubmit({
      x: defaultX || 0,
      y: defaultY,
      text: text.trim(),
      type,
    });
  };

  const types: Array<{ value: Annotation['type']; label: string; icon: React.ReactNode }> = [
    { value: 'note', label: 'Nota', icon: <MessageSquare className="w-4 h-4" /> },
    { value: 'alert', label: 'Alerta', icon: <AlertTriangle className="w-4 h-4" /> },
    { value: 'info', label: 'Info', icon: <Info className="w-4 h-4" /> },
    { value: 'milestone', label: 'Marco', icon: <Flag className="w-4 h-4" /> },
  ];

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-xl border border-slate-200 p-4 w-72">
      <h4 className="text-sm font-semibold text-slate-800 mb-3">Nova Anotação</h4>

      {/* Type selection */}
      <div className="flex gap-2 mb-3">
        {types.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => setType(t.value)}
            className={`flex-1 flex flex-col items-center gap-1 py-2 px-2 rounded-lg border transition-colors ${
              type === t.value
                ? 'border-blue-500 bg-blue-50 text-blue-600'
                : 'border-slate-200 hover:bg-slate-50 text-slate-600'
            }`}
          >
            {t.icon}
            <span className="text-xs">{t.label}</span>
          </button>
        ))}
      </div>

      {/* Text input */}
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Digite sua anotação..."
        className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-blue-400 resize-none"
        rows={3}
        autoFocus
      />

      {/* Actions */}
      <div className="flex gap-2 mt-3">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 px-3 py-2 text-sm text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={!text.trim()}
          className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 rounded-lg transition-colors"
        >
          <Check className="w-4 h-4" /> Salvar
        </button>
      </div>
    </form>
  );
};

// Main ChartAnnotation overlay component
export const ChartAnnotation: React.FC<ChartAnnotationProps> = ({
  annotations,
  onAdd,
  onEdit,
  onDelete,
  readOnly = false,
  className = '',
}) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [addPosition, setAddPosition] = useState<{ x: number; y: number } | null>(null);

  const handleChartClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (readOnly || !onAdd) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setAddPosition({ x, y });
    setShowAddForm(true);
  }, [readOnly, onAdd]);

  const handleAddAnnotation = (annotation: Omit<Annotation, 'id' | 'createdAt'>) => {
    onAdd?.(annotation);
    setShowAddForm(false);
    setAddPosition(null);
  };

  return (
    <div
      className={`relative ${className}`}
      onClick={handleChartClick}
      style={{ cursor: !readOnly && onAdd ? 'crosshair' : 'default' }}
    >
      {/* Annotations list (sidebar view) */}
      {annotations.length > 0 && (
        <div className="absolute top-2 right-2 z-20">
          <div className="bg-white/90 backdrop-blur-sm rounded-lg shadow-lg border border-slate-200 p-2 max-w-xs">
            <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-100">
              <MessageSquare className="w-4 h-4 text-slate-500" />
              <span className="text-xs font-medium text-slate-700">
                {annotations.length} {annotations.length === 1 ? 'Anotação' : 'Anotações'}
              </span>
            </div>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {annotations.slice(0, 5).map((ann) => (
                <div
                  key={ann.id}
                  className="flex items-start gap-2 p-1.5 rounded hover:bg-slate-50 text-xs"
                >
                  {ann.type === 'alert' ? (
                    <AlertTriangle className="w-3 h-3 text-red-500 mt-0.5 flex-shrink-0" />
                  ) : ann.type === 'info' ? (
                    <Info className="w-3 h-3 text-cyan-500 mt-0.5 flex-shrink-0" />
                  ) : ann.type === 'milestone' ? (
                    <Flag className="w-3 h-3 text-purple-500 mt-0.5 flex-shrink-0" />
                  ) : (
                    <MessageSquare className="w-3 h-3 text-blue-500 mt-0.5 flex-shrink-0" />
                  )}
                  <span className="text-slate-600 truncate">{ann.text}</span>
                </div>
              ))}
              {annotations.length > 5 && (
                <p className="text-xs text-slate-400 text-center pt-1">
                  +{annotations.length - 5} mais
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Add form overlay */}
      {showAddForm && addPosition && (
        <div
          className="absolute z-30"
          style={{ left: addPosition.x, top: addPosition.y }}
          onClick={(e) => e.stopPropagation()}
        >
          <AddAnnotationForm
            onSubmit={handleAddAnnotation}
            onCancel={() => {
              setShowAddForm(false);
              setAddPosition(null);
            }}
            defaultX={addPosition.x}
            defaultY={addPosition.y}
          />
        </div>
      )}

      {/* Add button hint */}
      {!readOnly && onAdd && annotations.length === 0 && (
        <div className="absolute bottom-2 right-2 z-10">
          <div className="flex items-center gap-1 px-2 py-1 bg-slate-100 rounded-full text-xs text-slate-500">
            <MessageSquare className="w-3 h-3" />
            Clique para adicionar anotação
          </div>
        </div>
      )}
    </div>
  );
};

// Hook for managing annotations state
export function useChartAnnotations(initialAnnotations: Annotation[] = []) {
  const [annotations, setAnnotations] = useState<Annotation[]>(initialAnnotations);

  const addAnnotation = useCallback((annotation: Omit<Annotation, 'id' | 'createdAt'>) => {
    const newAnnotation: Annotation = {
      ...annotation,
      id: `ann-${Date.now()}`,
      createdAt: new Date(),
    };
    setAnnotations((prev) => [...prev, newAnnotation]);
    return newAnnotation;
  }, []);

  const editAnnotation = useCallback((id: string, text: string) => {
    setAnnotations((prev) =>
      prev.map((ann) => (ann.id === id ? { ...ann, text } : ann))
    );
  }, []);

  const deleteAnnotation = useCallback((id: string) => {
    setAnnotations((prev) => prev.filter((ann) => ann.id !== id));
  }, []);

  const clearAnnotations = useCallback(() => {
    setAnnotations([]);
  }, []);

  return {
    annotations,
    addAnnotation,
    editAnnotation,
    deleteAnnotation,
    clearAnnotations,
    setAnnotations,
  };
}

export default ChartAnnotation;
