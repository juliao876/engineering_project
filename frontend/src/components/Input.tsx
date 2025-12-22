import React, { useState } from 'react';
import './Input.css';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  className?: string;
  enablePasswordToggle?: boolean;
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
      enablePasswordToggle = false,
      type = 'text',
      ...rest
    },
    ref
  ) => {
    const [isPasswordVisible, setIsPasswordVisible] = useState(false);

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

    const isPasswordField = type === 'password';
    const inputType = enablePasswordToggle && isPasswordField
      ? (isPasswordVisible ? 'text' : 'password')
      : type;

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
          <input ref={ref} className={fieldClasses} type={inputType} {...rest} />
          {icon && iconPosition === 'right' && !enablePasswordToggle && (
            <span className="input__icon input__icon--right">{icon}</span>
          )}
          {enablePasswordToggle && isPasswordField && (
            <button
              type="button"
              className="input__iconButton input__icon input__icon--right"
              aria-label={isPasswordVisible ? 'Hide password' : 'Show password'}
              onClick={() => setIsPasswordVisible((prev) => !prev)}
            >
              {icon || (isPasswordVisible ? '🙈' : '👁')}
            </button>
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