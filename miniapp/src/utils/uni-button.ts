export type TemplateButtonType = 'button' | 'submit' | 'reset'

// uni-app runtime supports themed button types, while vue-tsc narrows template
// <button> to native HTML values only.
export const UNI_BUTTON_TYPE = {
  primary: 'primary' as unknown as TemplateButtonType,
  warn: 'warn' as unknown as TemplateButtonType,
} as const
