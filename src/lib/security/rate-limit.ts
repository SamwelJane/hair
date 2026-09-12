import { redis } from "@/lib/queue/redis-client";

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  retryAfterSeconds: number;
}

/**
 * Fixed-window rate limiter keyed by an arbitrary identifier (IP, user id,
 * phone number, etc). Uses a single Redis key with INCR + EXPIRE so it works
 * across the multiple serverless invocations a Vercel deployment would have,
 * unlike an in-memory counter.
 */
export async function rateLimit(
  key: string,
  limit: number,
  windowSeconds: number
): Promise<RateLimitResult> {
  if (!process.env.REDIS_URL) {
    return { allowed: true, remaining: limit, retryAfterSeconds: 0 };
  }

  try {
    const redisKey = `ratelimit:${key}`;
    const count = await redis.incr(redisKey);

    if (count === 1) {
      await redis.expire(redisKey, windowSeconds);
    }

    const ttl = await redis.ttl(redisKey);
    const retryAfterSeconds = ttl > 0 ? ttl : windowSeconds;

    return {
      allowed: count <= limit,
      remaining: Math.max(0, limit - count),
      retryAfterSeconds,
    };
  } catch {
    return { allowed: true, remaining: limit, retryAfterSeconds: 0 };
  }
}

export function getClientIp(request: Request): string {
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) return forwarded.split(",")[0].trim();
  return request.headers.get("x-real-ip") ?? "unknown";
}
