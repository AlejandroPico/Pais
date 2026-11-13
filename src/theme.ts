export const themeOptions = [
  ['morning', 'Mañana'],
  ['afternoon', 'Tarde'],
  ['night', 'Noche'],
  ['auto', 'Automático'],
] as const;

export type Theme = typeof themeOptions[number][0];

export function readTheme(value: string | null): Theme {
  if (value === 'light') return 'morning';
  if (value === 'dark') return 'night';
  return themeOptions.some(([id]) => id === value) ? value as Theme : 'auto';
}

/** Approximate solar times at the atlas reference point, Madrid. */
export function solarTheme(now: Date): Exclude<Theme, 'auto'> {
  const radians = Math.PI / 180;
  const start = Date.UTC(now.getUTCFullYear(), 0, 1);
  const day = (now.getTime() - start) / 86_400_000;
  const angle = 2 * Math.PI * (day - 0.5) / 365.2422;
  const equation = 229.18 * (0.000075 + 0.001868 * Math.cos(angle)
    - 0.032077 * Math.sin(angle) - 0.014615 * Math.cos(2 * angle)
    - 0.040849 * Math.sin(2 * angle));
  const declination = 0.006918 - 0.399912 * Math.cos(angle) + 0.070257 * Math.sin(angle)
    - 0.006758 * Math.cos(2 * angle) + 0.000907 * Math.sin(2 * angle)
    - 0.002697 * Math.cos(3 * angle) + 0.00148 * Math.sin(3 * angle);
  const latitude = 40.4168 * radians;
  const hourAngle = Math.acos((Math.cos(90.833 * radians) - Math.sin(latitude) * Math.sin(declination))
    / (Math.cos(latitude) * Math.cos(declination)));
  const noon = 720 - 4 * (-3.7038) - equation;
  const daylightHalf = 4 * hourAngle / radians;
  const minute = now.getUTCHours() * 60 + now.getUTCMinutes();
  if (minute < noon - daylightHalf || minute >= noon + daylightHalf) return 'night';
  return minute < noon ? 'morning' : 'afternoon';
}
