from discord.ext import commands
import discord
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection

from bot import TIMEZONE
from bot.core.constant import DbCons


class EmbedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.embed_collection: AsyncIOMotorCollection = self.db[DbCons.EMBED_COLLECTION.value]

    async def get_preset(self, guild_id: int, name: str) -> dict | None:
        return await self.embed_collection.find_one({"guild_id": guild_id, "name": name})

    async def build_embed(self, preset: dict, user: discord.Member=None, server: discord.Guild=None, channel=None) -> discord.Embed:
        def replace_tokens(text: str) -> str:
            if not text:
                return ""
            return (
                text
                .replace("{user}", getattr(user, "mention", "{user}") if user else "{user}")
                .replace("{username}", user.display_name if user else "{username}")
                .replace("{avatar}", str(user.avatar.url) if user and user.avatar else " ")
                .replace("{owner_avatar}", str(server.owner.avatar.url) if server.owner and server.owner.avatar else " ")
                .replace("{server}", getattr(server, "name", "{server}") if server else "{server}")
                .replace("{server_icon}", str(server.icon.url) if server and server.icon else " ")
                .replace("{channel}", getattr(channel, "mention", "{channel}") if channel else " ")
                # 👇 NEW: turn the literal "\n" into an actual newline
                .replace("\\n", "\n")
                .replace("\in", "\u200B")
                .replace("{member_count}", str(server.member_count) if server else "0")
            )

        embed = discord.Embed(
            title=replace_tokens(preset.get("title")),
            description=replace_tokens(preset.get("description")),
            color=discord.Color.from_str(preset.get("color", "#5865F2")),
            timestamp=datetime.utcnow(),
        )
        if thumb := preset.get("thumbnail"):
            url = replace_tokens(thumb)
            if url != " ":
                embed.set_thumbnail(url=url)

        if img := preset.get("image"):
            url = replace_tokens(img)
            if url != " ":
                embed.set_image(url=url)

        if footer := preset.get("footer"):
            embed.set_footer(
                text=replace_tokens(footer.get("text", "")),
                icon_url=replace_tokens(footer.get("icon_url", "")),
            )
        for f in preset.get("fields", []):
            embed.add_field(
                name=replace_tokens(f["name"]),
                value=replace_tokens(f["value"]),
                inline=f.get("inline", False),
            )
        return embed


    @commands.hybrid_command(name="embed_preset_create", description="Creates or updates an embed preset with a title, description, and color.")
    @commands.has_permissions(administrator=True)
    async def embed_preset_create(self, ctx: commands.Context, name: str, title: str, description: str, color: str ="#5865F2" ):
        await ctx.defer()
        data = {
            "title": title,
            "description": description,
            "color" : color,
            "updated_at" : datetime.now(tz=TIMEZONE)
        }

        result = await self.embed_collection.update_one(
            {"guild_id": ctx.guild.id, "name": name},
            {
                "$set":data,
                "$setOnInsert" :{
                    "guild_id": ctx.guild.id,
                    "name": name,
                    "created_by": ctx.author.id,
                    "created_at": datetime.now(tz=TIMEZONE)
                }
            },
            upsert= True
        )

        if result.modified_count >0 or result.upserted_id:
            await ctx.send(f"✅ Preset `{name}` create/updated successfully.")
        else:
            await ctx.send(f"ℹ️ Preset `{name}` unchanged.")

    @commands.hybrid_command(name="embed_preset_set_footer", description="Sets the footer for an embed preset, including text and an optional icon.")
    @commands.has_permissions(administrator=True)
    async def embed_preset_set_footer(self, ctx: commands.Context,  name: str, text: str, icon_url: str = None):
        result = await self.embed_collection.update_one(
            {"guild_id": ctx.guild.id, "name": name},
            {
                "$set":{
                    "footer" :{"text": text, "icon_url": icon_url}
                }
            },
            upsert=True
        )

        if result.matched_count == 0:
            await ctx.send(f"❌ Preset `{name}` not found.")
        else:
            await ctx.send(f"✅ Footer updated for preset `{name}`.")

    @commands.hybrid_command(name="embed_preset_set_thumbnail", description="Sets the thumbnail image for an embed preset.")
    @commands.has_permissions(administrator=True)
    async def embed_preset_set_thumbnail(self, ctx: commands.Context, name: str, url: str):
        result = await self.embed_collection.update_one(
            {"guild_id": ctx.guild.id, "name": name},
            {"$set": {"thumbnail": url}},
        )
        if result.matched_count == 0:
            await ctx.send(f"❌ Preset `{name}` not found.")
        else:
            await ctx.send(f"✅ Thumbnail set for preset `{name}`.")

    @commands.hybrid_command(name="embed_preset_set_image", description="Sets the main image for an embed preset.")
    @commands.has_permissions(administrator=True)
    async def embed_preset_set_image(self, ctx: commands.Context, name: str, url: str):
        result = await self.embed_collection.update_one(
            {"guild_id": ctx.guild.id, "name": name},
            {"$set": {"image": url}},
        )
        if result.matched_count == 0:
            await ctx.send(f"❌ Preset `{name}` not found.")
        else:
            await ctx.send(f"✅ Image set for preset `{name}`.")

    @commands.hybrid_command(name="embed_preset_add_field", description="Adds a field with a title and value to an embed preset.")
    @commands.has_permissions(administrator=True)
    async def embed_preset_add_field(
            self,
            ctx: commands.Context,
            name: str,
            field_title: str,
            field_value: str,
            inline: bool = False,
    ):
        result = await self.embed_collection.update_one(
            {"guild_id": ctx.guild.id, "name": name},
            {"$push": {"fields": {"name": field_title, "value": field_value, "inline": inline}}},
        )
        if result.matched_count == 0:
            await ctx.send(f"❌ Preset `{name}` not found.")
        else:
            await ctx.send(f"✅ Field added to preset `{name}`.")

    @commands.hybrid_command(name="embed_preset_clear_fields", description="Removes all fields from an embed preset.")
    @commands.has_permissions(administrator=True)
    async def embed_preset_clear_fields(self, ctx: commands.Context, name: str):
        result = await self.embed_collection.update_one(
            {"guild_id": ctx.guild.id, "name": name},
            {"$set": {"fields": []}},
        )
        if result.matched_count == 0:
            await ctx.send(f"❌ Preset `{name}` not found.")
        else:
            await ctx.send(f"✅ All fields cleared for preset `{name}`.")

    @commands.hybrid_command(
        name="embed_preset_list",
        description="Lists all available embed presets in the server."
    )
    @commands.has_permissions(administrator=True)
    async def embed_preset_list(self, ctx: commands.Context):
        await ctx.defer()
        cursor = self.embed_collection.find({"guild_id": ctx.guild.id}, {"name": 1})
        names = [doc["name"] async for doc in cursor]
        if not names:
            await ctx.send("No presets found.")
            return
        await ctx.send("📑 Presets: " + ", ".join(f"`{n}`" for n in names))

    @commands.hybrid_command(
        name="embed_preset_show",
        description="Displays a preview of a saved embed preset."
    )
    async def embed_preset_show(self, ctx: commands.Context, name: str):
        await ctx.defer()
        preset = await self.get_preset(ctx.guild.id, name)
        if not preset:
            await ctx.send(f"❌ Preset `{name}` not found.")
            return
        embed = await self.build_embed(preset, user=ctx.author, server=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="embed_preset_post",
        description="Posts a saved embed preset to a specified channel."
    )
    @commands.has_permissions(manage_messages=True)
    async def embed_preset_post(
            self, ctx: commands.Context, name: str, channel: discord.TextChannel = None
    ):
        preset = await self.get_preset(ctx.guild.id, name)
        if not preset:
            await ctx.send(f"❌ Preset `{name}` not found.")
            return

        embed = await self.build_embed(preset, user=ctx.author, server=ctx.guild)
        channel = channel or ctx.channel
        await channel.send(embed=embed)
        await ctx.send(f"✅ Preset `{name}` posted to {channel.mention}", ephemeral=True)

    @commands.hybrid_command(
        name="embed_preset_delete",
        description="Deletes a saved embed preset."
    )
    @commands.has_permissions(administrator=True)
    async def embed_preset_delete(self, ctx: commands.Context, name: str):
        result = await self.embed_collection.delete_one({"guild_id": ctx.guild.id, "name": name})
        if result.deleted_count > 0:
            await ctx.send(f"🗑️ Preset `{name}` deleted.")
        else:
            await ctx.send(f"❌ Preset `{name}` not found.")



async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))