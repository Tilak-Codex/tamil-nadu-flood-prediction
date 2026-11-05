const RISK_LEVEL_LABELS = {
  NORMAL: 'Normal',
  WARNING: 'Above Normal',
  DANGER: 'Severe',
  CRITICAL: 'Extreme',
};

const RISK_CATEGORIES = [
  'Normal',
  'Above Normal',
  'Severe',
  'Extreme',
  'Threshold Unavailable',
];

export function getRiskCategory(summary = {}) {
  if (RISK_CATEGORIES.includes(summary.severity)) {
    return summary.severity;
  }

  if (RISK_CATEGORIES.includes(summary.risk_level)) {
    return summary.risk_level;
  }

  return RISK_LEVEL_LABELS[summary.risk_level] ?? 'Threshold Unavailable';
}
