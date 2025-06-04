import discord
from discord import Embed
from bot.core.models.guild_models import WelcomeEmbed


def build_welcome_embed(welcome_data: WelcomeEmbed):
    embed  = Embed(
        title= welcome_data.title,
        description= welcome_data.description,
        color = discord.Color.from_str(welcome_data.color) if welcome_data.color else discord.Color.default(),
    )

    if welcome_data.thumbnail_url:
        embed.set_thumbnail(url=welcome_data.thumbnail_url)
    
    if welcome_data.image_url:
        embed.set_image(url=welcome_data.image_url)

    if welcome_data.footer:
        embed.set_footer(text=welcome_data.footer)

    for field in welcome_data.fields:
        embed.add_field(
            name=field.name,
            value=field.value,
            inline=field.inline
        )
    return embed