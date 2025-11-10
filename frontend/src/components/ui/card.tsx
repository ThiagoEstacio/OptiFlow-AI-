import React from 'react';

type Props = React.HTMLAttributes<HTMLElement> & { children?: React.ReactNode };

export const Card: React.FC<Props> = ({ children, className, ...rest }) => (
  <div className={['bg-white', 'rounded-lg', 'shadow-sm', className].filter(Boolean).join(' ')} {...rest}>
    {children}
  </div>
);

export const CardHeader: React.FC<Props> = ({ children, className, ...rest }) => (
  <div className={['px-4', 'py-3', className].filter(Boolean).join(' ')} {...rest}>
    {children}
  </div>
);

export const CardTitle: React.FC<Props> = ({ children, className, ...rest }) => (
  <h3 className={['text-lg', 'font-semibold', className].filter(Boolean).join(' ')} {...rest}>
    {children}
  </h3>
);

export const CardContent: React.FC<Props> = ({ children, className, ...rest }) => (
  <div className={['px-4', 'py-4', className].filter(Boolean).join(' ')} {...rest}>
    {children}
  </div>
);

export default Card;
