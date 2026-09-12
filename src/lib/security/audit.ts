import { db } from "@/lib/db";

export interface LogAuditInput {
  userId?: string;
  action: string;
  entityType: string;
  entityId: string;
  metadata?: Record<string, unknown>;
}

export async function logAudit(input: LogAuditInput): Promise<void> {
  await db.auditLog.create({
    data: {
      userId: input.userId,
      action: input.action,
      entityType: input.entityType,
      entityId: input.entityId,
      metadata: input.metadata as object | undefined,
    },
  });
}
