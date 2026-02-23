/**
 * Program Calculation Service
 *
 * This module fetches calculation constants from the backend and provides
 * calculation functions that mirror the backend logic.
 *
 * IMPORTANT: This ensures frontend preview matches backend saved program exactly.
 *
 * Usage:
 * 1. Call fetchCalculationConstants() when program builder loads
 * 2. Use the calculation functions for real-time preview
 * 3. Backend will recalculate on save as source of truth
 */

// ============================================================================
// Types
// ============================================================================

export interface CalculationConstants {
  version: string;
  builder_type: string;
  weekly_jump_table: Record<number, number>;
  ramp_up_table: Record<number, number>;
  protocol_by_week: Record<number, { sets: number; reps: number }>;
}

export interface Movement {
  id: string;
  name: string;
  oneRM: number;
  eightyPercentRM: number;
  maxRepsAt80: number;
  weeklyJumpPercent: number;
  weeklyJumpLbs: number;
  rampUpPercent: number;
  rampUpBaseLbs: number;
  targetWeight: number;
}

// ============================================================================
// State
// ============================================================================

import { getToken } from './api';

let cachedConstants: CalculationConstants | null = null;

// ============================================================================
// API Functions
// ============================================================================

/**
 * Fetch calculation constants from backend.
 * Call this once when program builder loads.
 */
export async function fetchCalculationConstants(
  builderType: string = 'strength_linear_5x5'
): Promise<CalculationConstants> {
  try {
    const token = getToken();
    const headers: HeadersInit = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(
      `/api/v1/programs/algorithms/${builderType}/constants`,
      { headers }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch constants: ${response.statusText}`);
    }

    const constants = await response.json();
    cachedConstants = constants;

    console.log('✅ Loaded calculation constants from backend:', constants.version);
    return constants;
  } catch (error) {
    console.error('❌ Failed to fetch calculation constants:', error);
    // Fall back to hardcoded constants (not ideal, but keeps app working)
    return getFallbackConstants();
  }
}

/**
 * Get cached constants (fetch first if not cached).
 */
export async function getConstants(): Promise<CalculationConstants> {
  if (cachedConstants) {
    return cachedConstants;
  }
  return fetchCalculationConstants();
}

/**
 * Fallback constants if API fails (should match backend).
 * TODO: Remove this once backend is stable and always available.
 */
function getFallbackConstants(): CalculationConstants {
  console.warn('⚠️  Using fallback constants - frontend/backend may be out of sync!');

  return {
    version: 'v1.0.0-fallback',
    builder_type: 'strength_linear_5x5',
    weekly_jump_table: {
      20: 2, 19: 2, 18: 2, 17: 2, 16: 2,
      15: 3, 14: 3, 13: 3, 12: 3, 11: 3,
      10: 4, 9: 4, 8: 4, 7: 4, 6: 4,
      5: 5, 4: 5, 3: 5, 2: 5, 1: 5
    },
    ramp_up_table: {
      20: 70, 19: 69, 18: 68, 17: 67, 16: 66,
      15: 65, 14: 64, 13: 63, 12: 62, 11: 61,
      10: 60, 9: 59, 8: 58, 7: 57, 6: 56,
      5: 55, 4: 54, 3: 53, 2: 52, 1: 51
    },
    protocol_by_week: {
      1: { sets: 5, reps: 5 },
      2: { sets: 5, reps: 5 },
      3: { sets: 5, reps: 5 },
      4: { sets: 5, reps: 5 },
      5: { sets: 5, reps: 5 },
      6: { sets: 3, reps: 3 },
      7: { sets: 2, reps: 2 },
      8: { sets: 1, reps: 1 }
    }
  };
}

// ============================================================================
// Calculation Functions (mirror backend logic)
// ============================================================================

/**
 * Calculate 80% of 1RM.
 * Simple calculation - always the same.
 */
export function calculate80Percent(oneRM: number): number {
  return oneRM > 0 ? Math.round(oneRM * 0.8) : 0;
}

/**
 * Calculate weekly jump percentage and pounds.
 * Uses backend constants.
 */
export async function calculateWeeklyJump(
  maxRepsAt80: number,
  oneRM: number
): Promise<{ percent: number; lbs: number }> {
  const constants = await getConstants();

  const percent = constants.weekly_jump_table[maxRepsAt80] ?? 5; // Default to 5%
  const lbs = Math.round((oneRM * percent) / 100);

  return { percent, lbs };
}

/**
 * Calculate ramp-up percentage and base weight.
 * Uses backend constants.
 */
export async function calculateRampUp(
  maxRepsAt80: number,
  oneRM: number
): Promise<{ percent: number; baseLbs: number }> {
  const constants = await getConstants();

  const percent = constants.ramp_up_table[maxRepsAt80] ?? 55; // Default to 55%
  const baseLbs = Math.round((oneRM * percent) / 100);

  return { percent, baseLbs };
}

/**
 * Calculate weight for a specific week.
 * @param targetWeight - The target 5x5 weight (week 5)
 * @param weekNumber - Week number (1-8)
 * @param weeklyJumpLbs - Pounds to jump each week
 * @param isHeavy - Heavy day (true) or light day (false)
 */
export function calculateWeightForWeek(
  targetWeight: number,
  weekNumber: number,
  weeklyJumpLbs: number,
  isHeavy: boolean
): number {
  let heavyWeight: number;

  if (weekNumber <= 5) {
    // Linear progression toward target
    heavyWeight = targetWeight - ((5 - weekNumber) * weeklyJumpLbs);
  } else if (weekNumber === 6) {
    heavyWeight = targetWeight + weeklyJumpLbs;
  } else if (weekNumber === 7) {
    heavyWeight = targetWeight + (2 * weeklyJumpLbs);
  } else {
    // Week 8 is testing
    return 0;
  }

  // Light weight is 80% of heavy
  return isHeavy ? heavyWeight : Math.round(heavyWeight * 0.8);
}

/**
 * Calculate percentage of 1RM for display.
 */
export function calculatePercentage1RM(weight: number, oneRM: number): number {
  return weight > 0 && oneRM > 0 ? Math.round((weight / oneRM) * 100) : 0;
}

/**
 * Get sets and reps for a specific week.
 */
export async function getProtocolForWeek(
  weekNumber: number
): Promise<{ sets: number; reps: number }> {
  const constants = await getConstants();
  return constants.protocol_by_week[weekNumber] ?? { sets: 5, reps: 5 };
}

// ============================================================================
// Validation Function
// ============================================================================

/**
 * Validate frontend calculations against backend.
 * Call this before saving to ensure calculations match.
 *
 * @returns true if calculations match, false if mismatch detected
 */
export async function validateCalculations(
  movements: Movement[]
): Promise<{ valid: boolean; errors: string[] }> {
  try {
    // Prepare input data
    const inputData = {
      builder_type: 'strength_linear_5x5',
      movements: movements.map(m => ({
        name: m.name,
        one_rm: m.oneRM,
        max_reps_at_80_percent: m.maxRepsAt80,
        target_weight: m.targetWeight
      }))
    };

    // Call backend preview endpoint
    const token = getToken();
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch('/api/v1/programs/preview', {
      method: 'POST',
      headers,
      body: JSON.stringify(inputData)
    });

    if (!response.ok) {
      throw new Error(`Preview failed: ${response.statusText}`);
    }

    const backendPreview = await response.json();
    const errors: string[] = [];

    // Compare calculated data
    for (const movement of movements) {
      const backendCalc = backendPreview.calculated_data[movement.name];

      if (!backendCalc) {
        errors.push(`Backend did not calculate data for ${movement.name}`);
        continue;
      }

      // Check weekly jump
      if (backendCalc.weekly_jump_percent !== movement.weeklyJumpPercent) {
        errors.push(
          `${movement.name}: Weekly jump % mismatch - ` +
          `Frontend: ${movement.weeklyJumpPercent}, Backend: ${backendCalc.weekly_jump_percent}`
        );
      }

      if (backendCalc.weekly_jump_lbs !== movement.weeklyJumpLbs) {
        errors.push(
          `${movement.name}: Weekly jump lbs mismatch - ` +
          `Frontend: ${movement.weeklyJumpLbs}, Backend: ${backendCalc.weekly_jump_lbs}`
        );
      }

      // Check ramp up
      if (backendCalc.ramp_up_percent !== movement.rampUpPercent) {
        errors.push(
          `${movement.name}: Ramp up % mismatch - ` +
          `Frontend: ${movement.rampUpPercent}, Backend: ${backendCalc.ramp_up_percent}`
        );
      }

      if (backendCalc.ramp_up_base_lbs !== movement.rampUpBaseLbs) {
        errors.push(
          `${movement.name}: Ramp up base lbs mismatch - ` +
          `Frontend: ${movement.rampUpBaseLbs}, Backend: ${backendCalc.ramp_up_base_lbs}`
        );
      }
    }

    if (errors.length > 0) {
      console.error('❌ Calculation validation failed:', errors);
      return { valid: false, errors };
    }

    console.log('✅ Calculation validation passed!');
    return { valid: true, errors: [] };

  } catch (error) {
    console.error('❌ Validation error:', error);
    return {
      valid: false,
      errors: [`Validation failed: ${error instanceof Error ? error.message : 'Unknown error'}`]
    };
  }
}
