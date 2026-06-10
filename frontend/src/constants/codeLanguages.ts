export const CODE_LANGUAGE_OPTIONS = [
  { label: 'C', value: 'c' },
  { label: 'C++', value: 'cpp' },
  { label: 'Python', value: 'python' },
  { label: 'Java', value: 'java' },
] as const

export function languageLabel(value: string): string {
  const found = CODE_LANGUAGE_OPTIONS.find((item) => item.value === value)
  return found?.label ?? value
}
