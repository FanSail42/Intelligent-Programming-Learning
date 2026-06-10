/** ECharts 仪表盘统一色板（参考 Apache ECharts 默认配色） */
export const DASHBOARD_PALETTE = [
  '#5470c6',
  '#91cc75',
  '#fac858',
  '#ee6666',
  '#73c0de',
  '#3ba272',
  '#fc8452',
  '#9a60b4',
] as const

export const DASHBOARD_GRADIENT = {
  primary: ['#667eea', '#764ba2'] as [string, string],
  success: ['#11998e', '#38ef7d'] as [string, string],
  warning: ['#f7971e', '#ffd200'] as [string, string],
  danger: ['#eb3349', '#f45c43'] as [string, string],
  info: ['#4facfe', '#00f2fe'] as [string, string],
}

export function scoreColor(score: number): string {
  if (score < 60) return DASHBOARD_PALETTE[3]
  if (score < 80) return DASHBOARD_PALETTE[2]
  return DASHBOARD_PALETTE[1]
}

export function linearGradient(
  echarts: typeof import('echarts'),
  colors: [string, string],
  vertical = false,
) {
  return new echarts.graphic.LinearGradient(
    0,
    0,
    vertical ? 0 : 1,
    vertical ? 1 : 0,
    [
      { offset: 0, color: colors[0] },
      { offset: 1, color: colors[1] },
    ],
  )
}
