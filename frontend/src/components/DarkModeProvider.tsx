import React, { useEffect } from 'react';
import { useAppSelector } from '../store';

export const DarkModeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { theme } = useAppSelector((state) => state.ui);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  return <>{children}</>;
};
