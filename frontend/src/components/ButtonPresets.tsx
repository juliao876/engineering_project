import React from 'react';
import Button, { ButtonProps } from './Button.tsx';

export type ButtonPresetProps = Omit<ButtonProps, 'size' | 'variant'>;

export const ButtonS: React.FC<ButtonPresetProps> = (props) => (
  <Button size="small" variant="primary" {...props} />
);

export const ButtonSAlt: React.FC<ButtonPresetProps> = (props) => (
  <Button size="small" variant="secondary" {...props} />
);

export const ButtonM: React.FC<ButtonPresetProps> = (props) => (
  <Button size="medium" variant="primary" {...props} />
);

export const ButtonMAlt: React.FC<ButtonPresetProps> = (props) => (
  <Button size="medium" variant="secondary" {...props} />
);

export const ButtonL: React.FC<ButtonPresetProps> = (props) => (
  <Button size="large" variant="primary" {...props} />
);

export const ButtonLAlt: React.FC<ButtonPresetProps> = (props) => (
  <Button size="large" variant="secondary" {...props} />
);