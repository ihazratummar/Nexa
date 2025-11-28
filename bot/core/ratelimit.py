import time
import logging
from typing import Optional, Union, Callable
import discord
from discord.ext import commands
import redis.asyncio as redis

class RedisCooldown:
    def __init__(self, rate: int, per: float, type: Union[commands.BucketType, Callable[[commands.Context], str]]):
        self.rate = rate
        self.per = per
        self.type = type

    def get_key(self, ctx: commands.Context) -> str:
        if callable(self.type):
            key = self.type(ctx)
        elif self.type == commands.BucketType.default:
            key = "global"
        elif self.type == commands.BucketType.user:
            key = str(ctx.author.id)
        elif self.type == commands.BucketType.guild:
            key = str(ctx.guild.id) if ctx.guild else str(ctx.author.id)
        elif self.type == commands.BucketType.channel:
            key = str(ctx.channel.id)
        elif self.type == commands.BucketType.member:
            key = f"{ctx.guild.id}:{ctx.author.id}" if ctx.guild else str(ctx.author.id)
        elif self.type == commands.BucketType.category:
            key = str(ctx.channel.category_id) if ctx.channel.category else str(ctx.channel.id)
        elif self.type == commands.BucketType.role:
             key = str(ctx.author.top_role.id)
        else:
            key = "global"
        
        return f"ratelimit:{ctx.command.qualified_name}:{key}"

def redis_cooldown(rate: int, per: float, type: Union[commands.BucketType, Callable[[commands.Context], str]] = commands.BucketType.default):
    """
    A decorator that applies a Redis-backed cooldown to a command.
    """
    async def predicate(ctx: commands.Context):
        if not hasattr(ctx.bot, 'redis'):
            logging.warning("Redis not initialized in bot, skipping rate limit check.")
            return True

        cooldown = RedisCooldown(rate, per, type)
        key = cooldown.get_key(ctx)
        redis_client: redis.Redis = ctx.bot.redis

        # Use a Lua script for atomicity
        # Keys: [key]
        # Args: [rate, per]
        lua_script = """
        local key = KEYS[1]
        local rate = tonumber(ARGV[1])
        local per = tonumber(ARGV[2])
        
        local current = redis.call("LLEN", key)
        
        if current >= rate then
            local oldest = redis.call("LINDEX", key, -1)
            local now = tonumber(redis.call("TIME")[1]) + (tonumber(redis.call("TIME")[2]) / 1000000)
            if (now - tonumber(oldest)) < per then
                return per - (now - tonumber(oldest))
            end
        end
        
        redis.call("LPUSH", key, redis.call("TIME")[1] .. "." .. redis.call("TIME")[2])
        redis.call("LTRIM", key, 0, rate - 1)
        redis.call("EXPIRE", key, math.ceil(per))
        return 0
        """
        
        # Note: The above Lua script is a sliding window implementation. 
        # However, for simplicity and performance in high-scale, a fixed window or token bucket is often better.
        # Let's use a simpler Token Bucket / Fixed Window approach for now which is O(1).
        
        # Simple Fixed Window with Redis INCR
        # Key expires after 'per' seconds.
        
        current_time = int(time.time())
        # We bucket by time window to avoid race conditions resetting the counter
        # But standard INCR + EXPIRE is easier.
        
        # Let's stick to the standard discord.py bucket behavior but distributed.
        # We will use a simple counter.
        
        # Script to increment and set expire if new
        script = """
        local current = redis.call("INCR", KEYS[1])
        if current == 1 then
            redis.call("EXPIRE", KEYS[1], ARGV[1])
        end
        return current
        """
        
        try:
            current_usage = await redis_client.eval(script, 1, key, int(per))
            if current_usage > rate:
                # Calculate retry_after
                ttl = await redis_client.ttl(key)
                raise commands.CommandOnCooldown(
                    commands.Cooldown(rate, per), 
                    retry_after=ttl, 
                    type=type
                )
        except Exception as e:
            if isinstance(e, commands.CommandOnCooldown):
                raise e
            logging.error(f"Redis rate limit error: {e}")
            return True

        return True

    return commands.check(predicate)
