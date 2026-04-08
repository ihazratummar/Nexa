from typing import Optional

import discord
from discord import MediaGalleryItem

from bot.core.utils import help_loader
from bot.core.utils.help_loader import CommandCategory, CommandInfo


class HelpUi(discord.ui.LayoutView):
    """
    A dynamic LayoutView that displays command help from commands.yaml.

    Two display states, rendered within a single Container that is
    rebuilt on every interaction via ``_rebuild()``:

    1. **Command List** — paginated list (10/page) with prev/next buttons
    2. **Command Detail** — full info for one command with a back button

    Both states always show a command-select and a category-select at the bottom.
    """

    def __init__(self, *, author_id: int):
        super().__init__(timeout=120)

        # ── Who invoked /help ──
        self.author_id: int = author_id

        # ── State ──
        self.current_category: Optional[CommandCategory] = None
        self.current_page: int = 1
        self.viewing_command: Optional[CommandInfo] = None

        # Build the initial view
        self._rebuild()

    # ──────────────────────────────────────────────────────────
    # Interaction guard — only the invoking user can interact
    # ──────────────────────────────────────────────────────────

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "This help menu isn't for you!", ephemeral=True
            )
            return False
        return True

    # ──────────────────────────────────────────────────────────
    # Core rebuild
    # ──────────────────────────────────────────────────────────

    def _rebuild(self) -> None:
        """Clear everything and reconstruct the container from current state."""
        self.clear_items()

        container = discord.ui.Container(accent_color=discord.Color.blue())

        # ── Decide which state to render ──
        if self.viewing_command:
            self._build_detail_view(container)
        elif self.current_category:
            self._build_list_view(container)
        else:
            self._build_welcome_view(container)

        # ── Command select (only when a category is chosen) ──
        if self.current_category:
            commands_on_page, _ = help_loader.get_commands_page(
                self.current_category.id, self.current_page
            )
            if commands_on_page:
                cmd_select = discord.ui.Select(
                    placeholder="Select a command to view details…",
                    options=[
                        discord.SelectOption(
                            label=cmd.name,
                            value=cmd.name,
                            description=(cmd.description or "")[:100],
                        )
                        for cmd in commands_on_page
                    ],
                    min_values=1,
                    max_values=1,
                )
                cmd_select.callback = self._on_command_select
                container.add_item(discord.ui.ActionRow(cmd_select))

        # ── Category select (always visible) ──
        all_categories = help_loader.get_all_categories()
        cat_select = discord.ui.Select(
            placeholder="Select a category…",
            options=[
                discord.SelectOption(
                    label=cat.name,
                    value=cat.id,
                    description=(cat.description or "")[:100],
                    emoji=cat.emoji or None,
                    default=(
                        self.current_category is not None
                        and cat.id == self.current_category.id
                    ),
                )
                for cat in all_categories
            ],
            min_values=1,
            max_values=1,
        )
        cat_select.callback = self._on_category_select
        container.add_item(discord.ui.ActionRow(cat_select))

        self.add_item(container)

    # ──────────────────────────────────────────────────────────
    # Builders
    # ──────────────────────────────────────────────────────────

    def _build_welcome_view(self, container: discord.ui.Container) -> None:
        """Initial screen — prompts the user to pick a category."""
        container.add_item(
            discord.ui.TextDisplay("### ⚙️ Nexa Help")
        )
        container.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
        )
        container.add_item(discord.ui.TextDisplay("Select a category below to browse commands."))

        container.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
        )

    def _build_list_view(self, container: discord.ui.Container) -> None:
        """Paginated command list for the selected category."""
        cat = self.current_category
        commands_on_page, total_pages = help_loader.get_commands_page(
            cat.id, self.current_page
        )

        # Header
        emoji = cat.emoji or "📂"
        container.add_item(
            discord.ui.TextDisplay(f"### {emoji} {cat.name}")
        )
        if cat.description:
            container.add_item(
                discord.ui.TextDisplay(f"-# {cat.description}")
            )
        container.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
        )

        # Command list
        if commands_on_page:
            lines = []
            for cmd in commands_on_page:
                desc = cmd.description or "No description"
                lines.append(f"`{cmd.name}` — {desc}")
            container.add_item(
                discord.ui.TextDisplay("\n".join(lines))
            )
        else:
            container.add_item(
                discord.ui.TextDisplay("*No commands in this category.*")
            )

        container.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
        )

        # Page indicator + navigation
        container.add_item(
            discord.ui.TextDisplay(f"-# Page {self.current_page}/{total_pages}")
        )

        if total_pages > 1:
            prev_btn = discord.ui.Button(
                label="◀ Prev",
                style=discord.ButtonStyle.secondary,
                disabled=(self.current_page <= 1),
            )
            prev_btn.callback = self._on_prev

            next_btn = discord.ui.Button(
                label="Next ▶",
                style=discord.ButtonStyle.secondary,
                disabled=(self.current_page >= total_pages),
            )
            next_btn.callback = self._on_next

            container.add_item(discord.ui.ActionRow(prev_btn, next_btn))

        container.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
        )

    def _build_detail_view(self, container: discord.ui.Container) -> None:
        """Full detail view for a single command."""
        cmd = self.viewing_command

        # Header
        container.add_item(
            discord.ui.TextDisplay(f"### 📖 Command: {cmd.name}")
        )
        container.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
        )

        # Detail block
        detail_lines = []

        if cmd.description:
            detail_lines.append(f"**Description:** {cmd.description}")

        if cmd.usage:
            detail_lines.append(f"**Usage:** `{cmd.usage}`")

        if cmd.permissions:
            detail_lines.append(f"**Permissions:** {cmd.permissions}")

        if cmd.output:
            detail_lines.append(f"**Output:** {cmd.output}")

        if detail_lines:
            container.add_item(
                discord.ui.TextDisplay("\n".join(detail_lines))
            )

        # Arguments
        if cmd.args:
            arg_lines = ["**Arguments:**"]
            for arg in cmd.args:
                req = "required" if arg.required else "optional"
                arg_lines.append(f"╰ `{arg.name}` (*{arg.type}*, {req})")
                if arg.description:
                    arg_lines.append(f"  {arg.description}")
                if arg.example:
                    arg_lines.append(f"  Example: `{arg.example}`")
            container.add_item(
                discord.ui.TextDisplay("\n".join(arg_lines))
            )

        if cmd.notes:
            container.add_item(
                discord.ui.TextDisplay(f"**Notes:** {cmd.notes}")
            )

        container.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
        )

        # Back button
        back_btn = discord.ui.Button(
            label="◀ Back to list",
            style=discord.ButtonStyle.secondary,
        )
        back_btn.callback = self._on_back
        container.add_item(discord.ui.ActionRow(back_btn))

        container.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
        )

    # ──────────────────────────────────────────────────────────
    # Callbacks
    # ──────────────────────────────────────────────────────────

    async def _on_category_select(self, interaction: discord.Interaction) -> None:
        """User picked a category from the bottom select."""
        category_id = interaction.data["values"][0]
        self.current_category = help_loader.get_category(category_id)
        self.current_page = 1
        self.viewing_command = None
        self._rebuild()
        await interaction.response.edit_message(view=self)

    async def _on_command_select(self, interaction: discord.Interaction) -> None:
        """User picked a command to view its details."""
        command_name = interaction.data["values"][0]
        self.viewing_command = help_loader.get_command(command_name)
        self._rebuild()
        await interaction.response.edit_message(view=self)

    async def _on_prev(self, interaction: discord.Interaction) -> None:
        """Navigate to the previous page."""
        self.current_page = max(1, self.current_page - 1)
        self.viewing_command = None
        self._rebuild()
        await interaction.response.edit_message(view=self)

    async def _on_next(self, interaction: discord.Interaction) -> None:
        """Navigate to the next page."""
        self.current_page += 1
        self.viewing_command = None
        self._rebuild()
        await interaction.response.edit_message(view=self)

    async def _on_back(self, interaction: discord.Interaction) -> None:
        """Return from detail view to the command list."""
        self.viewing_command = None
        self._rebuild()
        await interaction.response.edit_message(view=self)
