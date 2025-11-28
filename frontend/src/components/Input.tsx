import React from 'react';
import './Input.css';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  className?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      error = false,
      fullWidth = true,
      icon,
      iconPosition = 'left',
      className = '',
      ...rest
    },
    ref
  ) => {
    const wrapperClasses = [
      'input',
      error ? 'input--error' : '',
      fullWidth ? 'input--fullWidth' : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    const fieldClasses = [
      'input__field',
      icon && iconPosition === 'left' ? 'input__field--withLeftIcon' : '',
      icon && iconPosition === 'right' ? 'input__field--withRightIcon' : '',
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <label className={wrapperClasses}>
        {label && (
          <span className="input__label">
            {label}
          </span>
        )}
        <div className="input__fieldWrapper">
          {icon && iconPosition === 'left' && (
            <span className="input__icon input__icon--left">{icon}</span>
          )}
          <input ref={ref} className={fieldClasses} {...rest} />
          {icon && iconPosition === 'right' && (
            <span className="input__icon input__icon--right">{icon}</span>
          )}
        </div>
        {helperText && (
          <span className="input__helper">{helperText}</span>
        )}
      </label>
    );
  }
);

Input.displayName = 'Input';

export default Input;