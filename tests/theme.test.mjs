import assert from 'node:assert/strict';
import test from 'node:test';
import {readTheme, solarTheme} from '../src/theme.ts';

test('automatic appearance follows daylight at different times of year', () => {
  assert.equal(solarTheme(new Date('2026-01-15T17:30:00Z')), 'night');
  assert.equal(solarTheme(new Date('2026-07-15T17:30:00Z')), 'afternoon');
  assert.equal(solarTheme(new Date('2026-07-15T08:00:00Z')), 'morning');
});

test('theme selection preserves stored preferences from earlier versions', () => {
  assert.equal(readTheme('light'), 'morning');
  assert.equal(readTheme('dark'), 'night');
  assert.equal(readTheme('afternoon'), 'afternoon');
  assert.equal(readTheme(null), 'auto');
});
