/**
 * useChartColors - Hook para aplicar cores suaves nos gráficos
 * ============================================================
 *
 * O Tremor/Recharts aplica atributos fill inline nos SVGs,
 * então precisamos usar JavaScript para sobrescrever após renderização.
 */
import { useEffect } from 'react';

const SLATE_500 = '#64748b';
const SLATE_600 = '#475569';
const SLATE_200 = '#e2e8f0';
const SLATE_100 = '#f1f5f9';

export const useChartColors = () => {
  useEffect(() => {
    const applyColors = () => {
      // Todos os textos SVG
      document.querySelectorAll('svg text').forEach((el) => {
        const element = el as SVGTextElement;
        const currentFill = element.getAttribute('fill');
        // Se for preto ou não definido, mudar para slate
        if (!currentFill || currentFill === '#000' || currentFill === '#000000' || currentFill === 'black' || currentFill === '#374151' || currentFill === '#1f2937' || currentFill === '#111827') {
          element.setAttribute('fill', SLATE_500);
        }
      });

      // Todos os tspans
      document.querySelectorAll('svg tspan').forEach((el) => {
        const element = el as SVGTSpanElement;
        const currentFill = element.getAttribute('fill');
        if (!currentFill || currentFill === '#000' || currentFill === '#000000' || currentFill === 'black' || currentFill === '#374151' || currentFill === '#1f2937' || currentFill === '#111827') {
          element.setAttribute('fill', SLATE_500);
        }
      });

      // Axis lines
      document.querySelectorAll('.recharts-cartesian-axis-line, .recharts-cartesian-axis-tick-line').forEach((el) => {
        (el as SVGElement).setAttribute('stroke', SLATE_200);
      });

      // Grid lines
      document.querySelectorAll('.recharts-cartesian-grid line').forEach((el) => {
        (el as SVGElement).setAttribute('stroke', SLATE_100);
      });
    };

    // Aplicar imediatamente
    applyColors();

    // Aplicar após pequeno delay (para gráficos que renderizam depois)
    const timeout1 = setTimeout(applyColors, 100);
    const timeout2 = setTimeout(applyColors, 500);
    const timeout3 = setTimeout(applyColors, 1000);

    // Observer para mudanças no DOM
    const observer = new MutationObserver((mutations) => {
      let shouldApply = false;
      mutations.forEach((mutation) => {
        if (mutation.addedNodes.length > 0) {
          mutation.addedNodes.forEach((node) => {
            if (node instanceof Element && (node.tagName === 'svg' || node.querySelector?.('svg'))) {
              shouldApply = true;
            }
          });
        }
      });
      if (shouldApply) {
        setTimeout(applyColors, 50);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    return () => {
      clearTimeout(timeout1);
      clearTimeout(timeout2);
      clearTimeout(timeout3);
      observer.disconnect();
    };
  }, []);
};

export default useChartColors;
