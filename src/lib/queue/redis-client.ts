import Redis from "ioredis";

const globalForRedis = globalThis as unknown as { redis: Redis | undefined };

export const redis =
  globalForRedis.redis ??
  new Redis(process.env.REDIS_URL ?? "redis://localhost:6379", {
    lazyConnect: true,
    maxRetriesPerRequest: 0,
    enableOfflineQueue: false,
  });

redis.on("error", () => {
  // Optional Redis services should not crash authentication or page rendering.
});

if (process.env.NODE_ENV !== "production") globalForRedis.redis = redis;
