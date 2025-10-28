import React, { useEffect } from 'react';
import { useAppSelector } from '../store';

export const DarkModeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { darkMode } = useAppSelector((state) => state.ui);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return <>{children}</>;
};
