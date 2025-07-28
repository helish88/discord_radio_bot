from typing import Optional
import aiohttp
import asyncio
import re
import disnake
from disnake.ext import commands
import wavelink


async def is_position_fresh(
    inter: disnake.ApplicationCommandInteraction | disnake.MessageInteraction,
) -> bool:
    messages = await inter.channel.history(limit=5).flatten()
    return (
        False
        if len(
            [
                message
                for message in messages
                if message.author.id != inter.bot.application_id
            ]
        )
        >= 5
        else True
    )


class RadioSearch(disnake.ui.View):
    def __init__(
        self,
        cmd_author: int,
        message: disnake.Message,
        vc: wavelink.Player,
    ):
        super().__init__(timeout=4000.00)
        self.cmd_author: int = cmd_author
        self.message: disnake.Message = message
        self.vc: wavelink.Player = vc
        self.current_url: Optional[str] = None
        self.update_radio.disabled = True
        self.radio_name: Optional[str] = " "

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.user.id != self.cmd_author:
            await interaction.response.send_message(
                embed=disnake.Embed(
                    color=disnake.Color.red(), title="This ain't your command to run"
                ),
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if self.vc.queue:
            await self.vc.queue.clear()
        await self.vc.stop()
        await self.vc.disconnect(force=True)
        self.stop()
        await self.message.delete()

    @disnake.ui.button(label="Find Radio", emoji="🔍", style=disnake.ButtonStyle.green)
    async def search_radio(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        await inter.response.send_modal(
            title="Please enter the radio name and country",
            custom_id=f"radio_search-{inter.id}",
            components=[
                disnake.ui.TextInput(
                    style=disnake.TextInputStyle.short,
                    label="Radio name",
                    placeholder="hit fm chisinau",
                    min_length=5,
                    max_length=20,
                    custom_id="radio_search",
                    required=True,
                )
            ],
        )
        try:
            modal_interaction = await inter.bot.wait_for(
                "modal_submit",
                check=lambda i: i.custom_id == f"radio_search-{inter.id}",
                timeout=200,
            )

        except asyncio.TimeoutError:
            return None

        radio_name_raw = modal_interaction.text_values["radio_search"]
        radio_name = radio_name_raw.replace(" ", "%20")
        async with aiohttp.request(
            "GET", url=f"http://radio.garden/api/search?q={radio_name}"
        ) as resp:
            raw_data = await resp.json()

        radio_posts = [
            disnake.SelectOption(
                label=f"{i.get('_source', None).get('title', ' ')} {i.get('_source', None).get('subtitle', ' ')}",
                value=i["_source"]["url"],
            )
            for i in raw_data["hits"]["hits"]
        ]
        components = [
            disnake.ui.Select(
                placeholder="Choose a radio",
                options=radio_posts,
                min_values=1,
                max_values=1,
                custom_id=f"radio_search-{inter.id}",
            )
        ]
        await modal_interaction.response.send_message(
            embed=disnake.Embed(
                color=disnake.Color.random(),
                title=f"Here are the results for your search `{radio_name_raw}`",
            ),
            components=components,
        )
        try:
            dropdown_interaction = await inter.bot.wait_for(
                "dropdown",
                check=lambda i: i.component.custom_id == f"radio_search-{inter.id}"
                and i.user.id == inter.user.id,
                timeout=200,
            )
        except asyncio.TimeoutError:
            return None
        selected_radio_url = dropdown_interaction.values[0]
        if match := re.search(
            r"/listen/(?P<radio_name>.+)/(?P<radio_id>.+)", selected_radio_url
        ):
            radio_link = match["radio_id"]
            url_to_play = (
                f"http://radio.garden/api/ara/content/listen/{radio_link}/channel.mp3"
            )
            self.current_url = url_to_play

        else:
            await dropdown_interaction.message.delete()
            return await dropdown_interaction.response.send_message(
                content="I can't play this radio stream", ephemeral=True
            )

        await dropdown_interaction.message.delete()
        try:
            track = await wavelink.Pool().fetch_tracks(url_to_play)
        except wavelink.LavalinkLoadException:
            return await dropdown_interaction.response.send_message(
                content="I can't play this radio stream", ephemeral=True
            )
        await self.vc.play(track[0])
        self.radio_name = radio_name_raw
        embed = disnake.Embed(
            color=disnake.Color.random(), title=f"Now playing {radio_name_raw}"
        ).set_footer(
            text="Radio not playing, try refreshing",
            icon_url=inter.user.display_avatar.url,
        )
        self.update_radio.disabled = False
        await modal_interaction.message.edit(embed=embed, view=self)
        return None  # ruff asked for this lul

    @disnake.ui.button(
        emoji="🔄", label="Refresh radio", style=disnake.ButtonStyle.green
    )
    async def update_radio(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ) -> None:
        if await is_position_fresh(inter=inter):
            track = await wavelink.Pool().fetch_tracks(self.current_url)
            await self.vc.play(track[0])

            await inter.response.send_message(
                content="Radio refreshed successfully", ephemeral=True
            )
        else:
            self.stop()
            await inter.message.delete()
            view = RadioSearch(
                cmd_author=inter.author.id, vc=self.vc, message=self.message
            )
            view.update_radio.disabled = False
            view.radio_name = self.radio_name
            view.current_url = self.current_url
            embed = disnake.Embed(
                color=disnake.Color.random(), title=f"Now playing {self.radio_name}"
            ).set_footer(
                text="Radio not playing, try refreshing",
                icon_url=inter.user.display_avatar.url,
            )
            await inter.response.send_message(embed=embed, view=view)

    @disnake.ui.button(
        emoji="<:trash:951421903095087164>", label="Stop", style=disnake.ButtonStyle.red
    )
    async def stop_radio(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ) -> None:
        self.vc.queue.clear()
        await self.vc.stop()
        try:
            await self.vc.disconnect(force=True)
        except ValueError:
            pass

        await inter.response.edit_message(view=None)
        await inter.message.delete()
        self.stop()


class Radio(
    commands.Cog,
    slash_command_attrs={"contexts": disnake.InteractionContextTypes(guild=True)},
    user_command_attrs={"contexts": disnake.InteractionContextTypes(guild=True)},
    message_command_attrs={"contexts": disnake.InteractionContextTypes(guild=True)},
):  # slash commands will work only in a discord server(not in DM)
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.wavelink_node_is_ready = False
        bot.loop.create_task(self.connect_nodes())

    def cog_unload(self) -> None:
        print("node canceled")
        self.bot.loop.create_task(self.dissconect_nodes())

    async def dissconect_nodes(self) -> None:
        node = wavelink.Pool().get_node()
        await node.close()

    async def connect_nodes(self) -> None:
        await self.bot.wait_until_ready()
        nodes = [wavelink.Node(uri="http://lavalink:2333", password="Qwert*9")]
        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=100)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(
        self, payload: wavelink.NodeReadyEventPayload
    ) -> None:
        self.wavelink_node_is_ready = True
        print(
            f"Radio Wavelink Node connected: {payload.node!r} | Resumed: {payload.resumed}"
        )

        # cache_capacity is EXPERIMENTAL. Turn it off by passing None

    @commands.slash_command(
        name="radio", description="Search and play any radio station wordwide"
    )
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def play_radio(self, inter: disnake.ApplicationCommandInteraction):
        if not self.wavelink_node_is_ready:
            return await inter.response.send_message(
                embed=disnake.Embed(
                    color=disnake.Color.red(),
                    title="Lavalink node aren't ready, try again in few seconds",
                ),
                ephemeral=True,
                delete_after=10,
            )
        if not inter.author.voice:
            return await inter.response.send_message(
                embed=disnake.Embed(
                    color=disnake.Color.red(),
                    description="You must be in a voice channel",
                ),
                ephemeral=True,
            )

        if inter.guild.me.voice:
            return await inter.response.send_message(
                content=f"I'm already connected to {inter.guild.me.voice.channel.mention}",
                ephemeral=True,
            )
        if (
            not inter.user.voice.channel.permissions_for(inter.guild.me).connect
            and not inter.user.voice.channel.permissions_for(inter.guild.me).speak
        ):
            return await inter.response.send_message(
                content=f"I don't have permissions to play in this channel {inter.user.voice.channel.mention}",
                ephemeral=True,
            )
        await inter.response.defer()
        vc: wavelink.Player = await inter.author.voice.channel.connect(
            cls=wavelink.Player
        )
        message = await inter.original_message()
        view = RadioSearch(cmd_author=inter.author.id, vc=vc, message=message)

        await inter.send(
            embed=disnake.Embed(
                color=disnake.Color.random(),
                description=f"Successfully connected to {inter.author.voice.channel.mention}\n"
                "Now click on  `Choose a radio`,\n"
                f"💡 For more precise results, include the country when searching",
            ),
            view=view,
        )
        return None  # ruff again

    @play_radio.error
    async def play_radio_error(
        self, inter: disnake.ApplicationCommandInteraction, error
    ):
        print(f"{error}\n{type(error)}")
        if isinstance(error, commands.CommandOnCooldown):
            return await inter.send(
                embed=disnake.Embed(
                    color=disnake.Color.red(),
                    description=f"{inter.user.mention} You'll be able to use the command in "
                    f"{error.retry_after:.2f} seconds",
                ),
                ephemeral=True,
                delete_after=10,
            )
        else:
            return await inter.send(
                embed=disnake.Embed(
                    color=disnake.Color.red(), description=f"``{error}```"
                ),
                ephemeral=True,
                delete_after=10,
            )


def setup(bot: commands.InteractionBot):
    bot.add_cog(Radio(bot))
    print("Radio is loaded.")
