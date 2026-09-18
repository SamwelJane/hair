// Mirrors backend/app/models/enums.py::PackageStatus. Kept in its own file
// rather than appended to orderStatus.ts — Order and Package are separate
// state machines and must not share one status value set.
export const PACKAGE_STATUS_VALUES = [
  "EXPECTED",
  "RECEIVED",
  "READY_FOR_CONSOLIDATION",
  "CONSOLIDATED",
  "IN_TRANSIT",
  "AT_CUSTOMS_KENYA",
  "READY_FOR_DELIVERY",
  "DELIVERED",
  "EXCEPTION",
] as const;

export type PackageStatus = (typeof PACKAGE_STATUS_VALUES)[number];
