/**
 * 🏭 Industrial Components - SCADA/IIoT Style
 * ============================================
 *
 * Componentes inspirados em sistemas industriais como:
 * - OSIsoft PI Vision
 * - Ignition SCADA
 * - Aveva Edge
 *
 * Padrões implementados:
 * - Quality indicators (Good/Bad/Uncertain/Stale)
 * - Communication failure indicators
 * - Asset hierarchy navigation
 */

export {
  QualityIndicator,
  TagValueWithQuality,
  CommFailIndicator,
  StaleDataBanner,
  type DataQuality,
  type QualityIndicatorProps,
  type TagValueWithQualityProps,
} from './QualityIndicator';
