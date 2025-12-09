/**
 * Module declarations for packages without TypeScript types
 */

declare module 'xlsx' {
  export const utils: {
    book_new: () => any;
    json_to_sheet: (data: any[]) => any;
    book_append_sheet: (workbook: any, sheet: any, name: string) => void;
    aoa_to_sheet: (data: any[][]) => any;
  };
  export const writeFile: (workbook: any, filename: string) => void;
}

declare module 'html2canvas' {
  interface Html2CanvasOptions {
    scale?: number;
    useCORS?: boolean;
    logging?: boolean;
    backgroundColor?: string;
  }

  function html2canvas(element: HTMLElement, options?: Html2CanvasOptions): Promise<HTMLCanvasElement>;
  export default html2canvas;
}

declare module 'react-draggable' {
  import { Component, ReactNode, CSSProperties } from 'react';

  interface DraggableProps {
    children: ReactNode;
    nodeRef?: React.RefObject<HTMLElement>;
    position?: { x: number; y: number };
    defaultPosition?: { x: number; y: number };
    onStart?: (e: any, data: any) => void | false;
    onDrag?: (e: any, data: any) => void | false;
    onStop?: (e: any, data: any) => void | false;
    bounds?: string | { left?: number; right?: number; top?: number; bottom?: number };
    disabled?: boolean;
    handle?: string;
    cancel?: string;
  }

  export default class Draggable extends Component<DraggableProps> {}
}
