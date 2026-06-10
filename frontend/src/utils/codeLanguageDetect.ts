import { languageLabel } from '@/constants/codeLanguages'

export type CodeLangValue = 'c' | 'cpp' | 'python' | 'java'

export interface LanguageMismatch {
  match: false
  suggested: CodeLangValue
  suggestedLabel: string
}

export interface LanguageMatch {
  match: true
}

export type LanguageCheckResult = LanguageMatch | LanguageMismatch

function scoreLanguages(code: string): Record<CodeLangValue, number> {
  const scores: Record<CodeLangValue, number> = { c: 0, cpp: 0, python: 0, java: 0 }
  const lower = code.toLowerCase()

  if (/^\s*def\s+\w+/m.test(code)) scores.python += 4
  if (/^\s*class\s+\w+.*:/m.test(code)) scores.python += 2
  if (/^\s*import\s+(?!java\.)\w+/m.test(code)) scores.python += 2
  if (/\belif\s+/m.test(code)) scores.python += 3
  if (/print\s*\(/m.test(code) && !/System\.out/.test(code)) scores.python += 2
  if (/:\s*$/m.test(code)) scores.python += 1
  if (/f["']/.test(code)) scores.python += 1

  if (/public\s+class\s+\w+/m.test(code)) scores.java += 4
  if (/System\.out\.print/m.test(code)) scores.java += 4
  if (/import\s+java\./m.test(code)) scores.java += 3
  if (/public\s+static\s+void\s+main\s*\(/m.test(code)) scores.java += 3
  if (/\bString\s*\[\]/m.test(code)) scores.java += 1

  if (/#include\s*<iostream>/m.test(code)) scores.cpp += 4
  if (/\bcout\s*<</m.test(code)) scores.cpp += 4
  if (/using\s+namespace\s+std/m.test(code)) scores.cpp += 3
  if (/\bstd::/m.test(code)) scores.cpp += 2
  if (/#include\s*<string>/m.test(code)) scores.cpp += 1

  if (/#include\s*<stdio\.h>/m.test(code)) scores.c += 4
  if (/printf\s*\(/m.test(code) && !/\bcout\b/.test(code)) scores.c += 3
  if (/int\s+main\s*\(/m.test(code) && !/public\s+class/.test(code)) scores.c += 2
  if (/#include\s*<stdlib\.h>/m.test(code)) scores.c += 1

  if (scores.cpp > 0 && scores.c > 0) {
    if (/iostream|cout|namespace\s+std|std::/.test(lower)) scores.c -= 2
    if (/stdio\.h|printf\s*\(/.test(lower) && !/iostream|cout/.test(lower)) scores.cpp -= 1
  }

  if (scores.python > 0 && scores.java > 0) {
    if (/System\.out|public\s+class/.test(code)) scores.python -= 2
    if (/^\s*def\s+/m.test(code)) scores.java -= 2
  }

  return scores
}

export function checkCodeLanguage(code: string, selected: string): LanguageCheckResult {
  const normalized = selected === 'c++' ? 'cpp' : selected
  if (!['c', 'cpp', 'python', 'java'].includes(normalized)) {
    return { match: true }
  }

  const scores = scoreLanguages(code)
  const selectedKey = normalized as CodeLangValue
  const selectedScore = scores[selectedKey]

  const ranked = (Object.entries(scores) as [CodeLangValue, number][])
    .sort((a, b) => b[1] - a[1])
  const [topLang, topScore] = ranked[0]

  if (topScore === 0 && selectedScore === 0) {
    return { match: true }
  }

  if (topLang !== selectedKey && topScore >= 2 && topScore > selectedScore + 1) {
    return {
      match: false,
      suggested: topLang,
      suggestedLabel: languageLabel(topLang),
    }
  }

  return { match: true }
}
