// Mirrors backend/app/models/enums.py::ConsolidationStatus. Kept in its own
// file, separate from Order/Package status - Consolidation is its own state
// machine (see packageStatus.ts for why these aren't merged).
export const CONSOLIDATION_STATUS_VALUES = [
  "OPEN",
  "READY_FOR_EXPORT",
  "DEPARTED",
  "IN_TRANSIT",
  "ARRIVED",
  "CLOSED",
] as const;

export type ConsolidationStatus = (typeof CONSOLIDATION_STATUS_VALUES)[number];
