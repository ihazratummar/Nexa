from typing import List

import discord

from core.constant import Color
from modules.moderation.model import ModerationLogModel
from modules.moderation.services import ModerationService


async def warning_embed(
        guild: discord.Guild,
        warning_logs: List[ModerationLogModel],
        offender: discord.Member
) -> discord.Embed:
    if warning_logs is None:
        color = discord.Color.from_str(Color.PRIMARY_COLOR)
        warning_embed = discord.Embed(
            color=color,
            timestamp=discord.utils.utcnow(),
            description="🕯️ The scroll remains clean. No warnings have been written.",
        )
    else:
        warning_embed = discord.Embed(
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
            type="rich"
        )
        warning_embed.set_author(
            name=f"{len(warning_logs)} Warnings for {offender.name}({offender.id})",
            icon_url=offender.avatar.url if offender.avatar else None
        )

        for log in warning_logs:
            moderator: discord.Member = guild.get_member(log.moderator_id)
            warning_embed.add_field(
                name=f"Moderator: {moderator.name}",
                value=f"{log.reason if log.reason is not None else ''} - <t:{int(log.created_at.timestamp())}:R>",
                inline=False
            )
    return warning_embed


class DeleteWarningsLogsUi(discord.ui.View):
    def __init__(self, offender: discord.Member, logs: List[ModerationLogModel]) -> None:
        super().__init__(timeout=300)
        self.offender = offender
        self.logs = logs

        self.delete_warnings_button = discord.ui.Button(
            label="Delete Warnings",
            style=discord.ButtonStyle.danger,
            custom_id="delete_warnings",
            emoji="🗑️"
        )
        self.delete_warnings_button.callback = self.delete_warnings
        if self.logs:
            self.add_item(self.delete_warnings_button)

    async def refresh(self, interaction: discord.Interaction) -> None:
        self.clear_items()

        logs = await ModerationService.get_offense_logs(
            guild_id=interaction.guild.id,
            offender_id=self.offender.id
        )

        embed = await warning_embed(
            guild=interaction.guild,
            warning_logs= logs ,
            offender=self.offender
        )

        if logs:
            self.add_item(self.delete_warnings_button)

        if interaction:
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)


    async def delete_warnings(self, interaction: discord.Interaction) -> None:

        resolved = await ModerationService.resolve_offense_logs(
            guild_id= interaction.guild.id,
            offender_id= self.offender.id,
            action_type="Warn"
        )
        if resolved > 0:
            self.delete_warnings_button.disabled = True

        try:
            message = f"The past is buried… but not forgotten. Walk carefully in {interaction.guild.name} from here on."
            await self.offender.send(message)
        except discord.Forbidden:
            pass


        await self.refresh(interaction= interaction)




