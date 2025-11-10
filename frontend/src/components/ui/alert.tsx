import React from 'react';

type Props = React.HTMLAttributes<HTMLElement> & { children?: React.ReactNode };

export const Alert: React.FC<Props & { variant?: 'default' | 'destructive' }> = ({
  children,
  className,
  variant = 'default',
  ...rest
}) => (
  <div
    role="alert"
    className={[
      'rounded-md',
      'p-3',
      variant === 'destructive' ? 'bg-red-50 border border-red-200 text-red-800' : 'bg-gray-50 border border-gray-200 text-gray-800',
      className,
    ]
      .filter(Boolean)
      .join(' ')}
    {...rest}
  >
    <div className="flex items-start gap-2">{children}</div>
  </div>
);

export const AlertDescription: React.FC<Props> = ({ children, className, ...rest }) => (
  <div className={['text-sm', className].filter(Boolean).join(' ')} {...rest}>
    {children}
  </div>
);

export default Alert;
