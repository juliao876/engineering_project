import React from 'react';
import './Button.css';

type ButtonSize = 'small' | 'medium' | 'large';
type ButtonVariant = 'primary' | 'secondary' | 'accent' | 'ghost';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: ButtonSize;
  variant?: ButtonVariant;
  fullWidth?: boolean;
  className?: string;
  forceHover?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  size = 'medium',
  variant = 'primary',
  fullWidth = false,
  className = '',
  forceHover = false,
  children,
  ...props
}) => {
  const classes = [
    'button',
    `button--${size}`,
    `button--${variant}`,
    fullWidth ? 'button--fullWidth' : '',
    forceHover ? 'is-hovered' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
};

export default Button;