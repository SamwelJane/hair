export function generateOrderNumber(): string {
  const now = new Date();
  const datePart = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}${String(
    now.getDate()
  ).padStart(2, "0")}`;
  const randomPart = Math.floor(1000 + Math.random() * 9000);
  return `ORD-${datePart}-${randomPart}`;
}
