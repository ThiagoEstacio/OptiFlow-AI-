/**
 * Internationalization (i18n) System
 * ===================================
 *
 * Sistema de internacionalização leve para OptiFlow.
 * Suporta PT-BR, EN-US e ES-ES.
 */
import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

// Import locale files
import ptBR from './locales/pt-BR.json';
import enUS from './locales/en-US.json';
import esES from './locales/es-ES.json';

export type Locale = 'pt-BR' | 'en-US' | 'es-ES';

export interface LocaleConfig {
  code: Locale;
  name: string;
  nativeName: string;
  flag: string;
  dateFormat: string;
  numberFormat: {
    decimal: string;
    thousand: string;
  };
}

export const locales: Record<Locale, LocaleConfig> = {
  'pt-BR': {
    code: 'pt-BR',
    name: 'Portuguese (Brazil)',
    nativeName: 'Português (Brasil)',
    flag: '🇧🇷',
    dateFormat: 'dd/MM/yyyy',
    numberFormat: { decimal: ',', thousand: '.' },
  },
  'en-US': {
    code: 'en-US',
    name: 'English (US)',
    nativeName: 'English (US)',
    flag: '🇺🇸',
    dateFormat: 'MM/dd/yyyy',
    numberFormat: { decimal: '.', thousand: ',' },
  },
  'es-ES': {
    code: 'es-ES',
    name: 'Spanish (Spain)',
    nativeName: 'Español (España)',
    flag: '🇪🇸',
    dateFormat: 'dd/MM/yyyy',
    numberFormat: { decimal: ',', thousand: '.' },
  },
};

// Translation dictionaries
const translations: Record<Locale, Record<string, any>> = {
  'pt-BR': ptBR,
  'en-US': enUS,
  'es-ES': esES,
};

// Get nested value from object using dot notation
const getNestedValue = (obj: any, path: string): string | undefined => {
  return path.split('.').reduce((current, key) => current?.[key], obj);
};

// Translation function type
type TranslateFunction = (key: string, params?: Record<string, string | number>) => string;

// i18n Context
interface I18nContextType {
  locale: Locale;
  localeConfig: LocaleConfig;
  setLocale: (locale: Locale) => void;
  t: TranslateFunction;
  formatNumber: (value: number, options?: Intl.NumberFormatOptions) => string;
  formatDate: (date: Date | string, options?: Intl.DateTimeFormatOptions) => string;
  formatCurrency: (value: number, currency?: string) => string;
}

const I18nContext = createContext<I18nContextType | null>(null);

// Storage key
const LOCALE_STORAGE_KEY = 'optiflow_locale';

// Detect browser locale
const detectBrowserLocale = (): Locale => {
  const browserLang = navigator.language;

  if (browserLang.startsWith('pt')) return 'pt-BR';
  if (browserLang.startsWith('es')) return 'es-ES';
  if (browserLang.startsWith('en')) return 'en-US';

  return 'pt-BR'; // Default
};

// i18n Provider Component
interface I18nProviderProps {
  children: React.ReactNode;
  defaultLocale?: Locale;
}

export const I18nProvider: React.FC<I18nProviderProps> = ({
  children,
  defaultLocale,
}) => {
  const [locale, setLocaleState] = useState<Locale>(() => {
    // Try to get from storage
    const stored = localStorage.getItem(LOCALE_STORAGE_KEY) as Locale;
    if (stored && locales[stored]) return stored;

    // Use default or detect
    return defaultLocale || detectBrowserLocale();
  });

  const localeConfig = locales[locale];

  // Save locale to storage
  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem(LOCALE_STORAGE_KEY, newLocale);
    document.documentElement.lang = newLocale;
  }, []);

  // Set document language on mount
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  // Translation function
  const t: TranslateFunction = useCallback(
    (key: string, params?: Record<string, string | number>) => {
      const translation = getNestedValue(translations[locale], key);

      if (!translation) {
        console.warn(`Missing translation: ${key} for locale ${locale}`);
        // Fallback to pt-BR or return key
        return getNestedValue(translations['pt-BR'], key) || key;
      }

      // Replace parameters
      if (params && typeof translation === 'string') {
        return Object.entries(params).reduce(
          (text, [param, value]) => text.replace(`{{${param}}}`, String(value)),
          translation
        );
      }

      return translation;
    },
    [locale]
  );

  // Format number
  const formatNumber = useCallback(
    (value: number, options?: Intl.NumberFormatOptions) => {
      return new Intl.NumberFormat(locale, options).format(value);
    },
    [locale]
  );

  // Format date
  const formatDate = useCallback(
    (date: Date | string, options?: Intl.DateTimeFormatOptions) => {
      const d = typeof date === 'string' ? new Date(date) : date;
      return new Intl.DateTimeFormat(locale, {
        dateStyle: 'short',
        timeStyle: 'short',
        ...options,
      }).format(d);
    },
    [locale]
  );

  // Format currency
  const formatCurrency = useCallback(
    (value: number, currency: string = 'BRL') => {
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency,
      }).format(value);
    },
    [locale]
  );

  const contextValue: I18nContextType = {
    locale,
    localeConfig,
    setLocale,
    t,
    formatNumber,
    formatDate,
    formatCurrency,
  };

  return React.createElement(I18nContext.Provider, { value: contextValue }, children);
};

// Hook to use i18n
export const useI18n = (): I18nContextType => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
};

// Simple hook for just translations
export const useTranslation = () => {
  const { t, locale } = useI18n();
  return { t, locale };
};

// Language Selector Component
export const LanguageSelector: React.FC<{
  variant?: 'dropdown' | 'buttons' | 'compact';
  className?: string;
}> = ({ variant = 'dropdown', className = '' }) => {
  const { locale, setLocale, localeConfig } = useI18n();
  const [isOpen, setIsOpen] = React.useState(false);

  if (variant === 'buttons') {
    return React.createElement(
      'div',
      { className: `flex gap-1 ${className}` },
      Object.values(locales).map((loc) =>
        React.createElement(
          'button',
          {
            key: loc.code,
            onClick: () => setLocale(loc.code),
            className: `px-2 py-1 text-sm rounded ${
              locale === loc.code
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`,
            title: loc.nativeName,
          },
          loc.flag
        )
      )
    );
  }

  if (variant === 'compact') {
    return React.createElement(
      'button',
      {
        onClick: () => {
          const localeList = Object.keys(locales) as Locale[];
          const currentIndex = localeList.indexOf(locale);
          const nextLocale = localeList[(currentIndex + 1) % localeList.length];
          setLocale(nextLocale);
        },
        className: `flex items-center gap-1 px-2 py-1 text-sm rounded hover:bg-slate-100 ${className}`,
        title: 'Alterar idioma',
      },
      React.createElement('span', null, localeConfig.flag),
      React.createElement('span', { className: 'text-xs text-slate-500' }, locale.split('-')[0].toUpperCase())
    );
  }

  // Dropdown variant
  return React.createElement(
    'div',
    { className: `relative ${className}` },
    React.createElement(
      'button',
      {
        onClick: () => setIsOpen(!isOpen),
        className: 'flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-slate-200 hover:bg-slate-50',
      },
      React.createElement('span', null, localeConfig.flag),
      React.createElement('span', null, localeConfig.nativeName),
      React.createElement(
        'svg',
        {
          className: `w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`,
          fill: 'none',
          viewBox: '0 0 24 24',
          stroke: 'currentColor',
        },
        React.createElement('path', {
          strokeLinecap: 'round',
          strokeLinejoin: 'round',
          strokeWidth: 2,
          d: 'M19 9l-7 7-7-7',
        })
      )
    ),
    isOpen &&
      React.createElement(
        'div',
        {
          className: 'absolute top-full left-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-50',
        },
        Object.values(locales).map((loc) =>
          React.createElement(
            'button',
            {
              key: loc.code,
              onClick: () => {
                setLocale(loc.code);
                setIsOpen(false);
              },
              className: `w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-slate-50 ${
                locale === loc.code ? 'bg-blue-50 text-blue-600' : 'text-slate-700'
              }`,
            },
            React.createElement('span', null, loc.flag),
            React.createElement('span', null, loc.nativeName)
          )
        )
      )
  );
};

export default {
  I18nProvider,
  useI18n,
  useTranslation,
  LanguageSelector,
  locales,
};
