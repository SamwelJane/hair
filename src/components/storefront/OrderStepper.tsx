import { CLIENT_STEPPER_GROUPS } from "@/lib/orders/state-machine";
import type { OrderStatus } from "@/generated/prisma/client";

export function OrderStepper({ status }: { status: OrderStatus }) {
  const currentIndex = CLIENT_STEPPER_GROUPS.findIndex((g) => g.statuses.includes(status));

  return (
    <ol className="flex flex-wrap gap-2 text-xs">
      {CLIENT_STEPPER_GROUPS.map((group, i) => {
        const isDone = i < currentIndex;
        const isCurrent = i === currentIndex;
        return (
          <li
            key={group.label}
            className={`rounded-full px-3 py-1 ${
              isCurrent
                ? "bg-brand-accent text-white"
                : isDone
                  ? "bg-brand-success/10 text-brand-success"
                  : "bg-brand-accent-soft text-brand-muted"
            }`}
          >
            {group.label}
          </li>
        );
      })}
    </ol>
  );
}
