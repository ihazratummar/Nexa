import discord

class LinksButton(discord.ui.View):
    def __init__(self, buttons_list: list[(str, str, str)]):
        self.button_list = buttons_list
        super().__init__()

        for label, link, emoji in self.button_list:
            self.add_item(discord.ui.Button(label=label, url= link, emoji = emoji))