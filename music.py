import discord
from discord.ext import commands
import lavalink
from lavalink.events import TrackStartEvent, QueueEndEvent
from lavalink.errors import ClientError
from lavalink.filters import Equalizer, LowPass, Timescale
from lavalink.server import LoadType
from discord import Intents
from discord import Embed
import re

url_rx = re.compile(r'https?://(?:www\.)?.+')

class MusicBot(commands.Bot):
    def __init__(self):
        intents = Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix=commands.when_mentioned_or("!"), intents=intents)
        self.lavalink = None

        # Remove the default help command
        self.remove_command('help')

        # Add a new help command
        @self.command()
        async def help(ctx):
            embed = Embed(title="Help", description="nope", color=0x115599)
        @self.command()
        async def sfw(ctx):
            embed = Embed(title="Help", description="nope", color=0x115599)
            
        @self.command()
        async def nsfw(ctx):
            embed = Embed(title="Help", description="nope", color=0x115599)
            
        @self.command()
        async def waifu(ctx):
            embed = Embed(title="Help", description="nope", color=0x115599)
            
        @self.command()
        async def botinfo(ctx):
            embed = Embed(title="Help", description="nope", color=0x115599)
            
        @self.command()
        async def purge(ctx):
            embed = Embed(title="Help", description="nope", color=0x115599)
            
        @self.command()
        async def generate(ctx):
            embed = Embed(title="Help", description="nope", color=0x115599)
            

    async def on_ready(self):
        print(f'Logged in as: {self.user.name}')
        print(f'With ID: {self.user.id}')
        self.lavalink = lavalink.Client(self.user.id)
        self.lavalink.add_node('127.0.0.1', 6969, 'youshallnotpass', 'na', 'music-node')
        self.add_listener(self.lavalink.voice_update_handler, 'on_socket_response')
        
        await self.add_cog(Music(self))

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            embed = Embed(title="Error", description="Command not found.", color=discord.Color.red())
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = Embed(title="Error", description="Missing required argument.", color=discord.Color.red())
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CheckFailure):
            embed = Embed(title="Error", description="You do not have the necessary permissions to execute this command.", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            embed = Embed(title="Error", description="An error occurred while executing the command.", color=discord.Color.red())
            await ctx.send(embed=embed)
            raise error

class LavalinkVoiceClient(discord.VoiceProtocol):
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        self.guild_id = channel.guild.id
        self._destroyed = False

        if not hasattr(self.client, 'lavalink'):
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node(host='localhost', port=2333, password='youshallnotpass',
                                          region='us', name='default-node')

        self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        lavalink_data = {
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        channel_id = data['channel_id']

        if not channel_id:
            await self._destroy()
            return

        self.channel = self.client.get_channel(int(channel_id))

        lavalink_data = {
            't': 'VOICE_STATE_UPDATE',
            'd': data
        }

        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def _destroy(self):
        self.cleanup()

        if self._destroyed:
            return

        self._destroyed = True

        try:
            await self.lavalink.player_manager.destroy(self.guild_id)
        except ClientError:
            pass


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(host='localhost', port=2333, password='youshallnotpass',
                                  region='us', name='default-node')

        self.lavalink: lavalink.Client = bot.lavalink
        self.lavalink.add_event_hooks(self)

    def cog_unload(self):
        self.lavalink._event_hooks.clear()

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            embed = Embed(title="Error", description=str(error.original), color=discord.Color.red())
            await ctx.send(embed=embed)

    async def create_player(ctx: commands.Context):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        player = ctx.bot.lavalink.player_manager.create(ctx.guild.id)
        should_connect = ctx.command.name in ('play',)

        voice_client = ctx.voice_client

        if not ctx.author.voice or not ctx.author.voice.channel:
            if voice_client is not None:
                raise commands.CommandInvokeError('You need to join a voice channel first.')

            raise commands.CommandInvokeError('Join a voice channel first.')

        voice_channel = ctx.author.voice.channel

        if voice_client is None:
            if not should_connect:
                raise commands.CommandInvokeError("I'm not playing music.")

            permissions = voice_channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:
                raise commands.CommandInvokeError('I need the `CONNECT` and `SPEAK` permissions.')

            if voice_channel.user_limit > 0:
                if len(voice_channel.members) >= voice_channel.user_limit and not ctx.me.guild_permissions.move_members:
                    raise commands.CommandInvokeError('Your voice channel is full!')

            player.store('channel', ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
        elif voice_client.channel.id != voice_channel.id:
            raise commands.CommandInvokeError('You need to be in a voice channel.')

        return True

    @lavalink.listener(TrackStartEvent)
    async def on_track_start(self, event: TrackStartEvent):
        guild_id = event.player.guild_id
        channel_id = event.player.fetch('channel')
        guild = self.bot.get_guild(guild_id)

        if not guild:
            return await self.lavalink.player_manager.destroy(guild_id)

        channel = guild.get_channel(channel_id)

        if channel:
            embed = Embed(title="Now Playing", description=f"{event.track.title} by {event.track.author}", color=discord.Color.green())
            await channel.send(embed=embed)

            # Apply audio filters for better quality
            equalizer = Equalizer()
            equalizer.update([(0, 0.1), (1, 0.1), (2, 0.1), (3, 0.1), (4, 0.1), (5, 0.1), (6, 0.1), (7, 0.1), (8, 0.1), (9, 0.1), (10, 0.1), (11, 0.1), (12, 0.1), (13, 0.1), (14, 0.1)])
            await event.player.set_filter(equalizer)
            await event.player.set_filter(LowPass(smoothing=20.0))
            await event.player.set_filter(Timescale(speed=1.0, pitch=1.0, rate=1.0))

    @lavalink.listener(QueueEndEvent)
    async def on_queue_end(self, event: QueueEndEvent):
        guild_id = event.player.guild_id
        guild = self.bot.get_guild(guild_id)

        if guild is not None:
            await guild.voice_client.disconnect(force=True)
            embed = Embed(title="Queue Ended", description="Disconnected from the voice channel.", color=discord.Color.orange())
            await self.bot.get_channel(event.player.fetch('channel')).send(embed=embed)

    @commands.command(aliases=['p'])
    @commands.check(create_player)
    async def play(self, ctx, *, query: str):
        try:
            player = self.bot.lavalink.player_manager.get(ctx.guild.id)
            query = query.strip('<>')

            if not url_rx.match(query):
                query = f'ytsearch:{query}'

            results = await player.node.get_tracks(query)

            embed = discord.Embed(color=discord.Color.blurple())

            if results.load_type == LoadType.EMPTY:
                embed.title = "Error"
                embed.description = "I couldn't find any tracks for that query."
                return await ctx.send(embed=embed)
            elif results.load_type == LoadType.PLAYLIST:
                tracks = results.tracks

                for track in tracks:
                    player.add(track=track, requester=ctx.author.id)

                embed.title = 'Playlist Enqueued!'
                embed.description = f'{results.playlist_info.name} - {len(tracks)} tracks'
            else:
                track = results.tracks[0]
                embed.title = 'Track Enqueued'
                embed.description = f'[{track.title}]({track.uri})'

                player.add(track=track, requester=ctx.author.id)

            await ctx.send(embed=embed)

            if not player.is_playing:
                await player.play()
        except Exception as e:
            embed = Embed(title="Error", description=f"An error occurred while trying to play the track: {str(e)}", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command()
    @commands.check(create_player)
    async def stop(self, ctx):
        try:
            player = self.bot.lavalink.player_manager.get(ctx.guild.id)

            # Get the name of the currently playing track
            track_name = player.current.title if player.current else "unknown track"

            player.queue.clear()
            await player.stop()

            embed = Embed(title="Stopped Playing", description=f'Stopped playing {track_name}.', color=discord.Color.red())
            await ctx.send(embed=embed)
        except Exception as e:
            embed = Embed(title="Error", description=f"An error occurred while trying to stop the track: {str(e)}", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command()
    @commands.check(create_player)
    async def skip(self, ctx):
        try:
            player = self.bot.lavalink.player_manager.get(ctx.guild.id)
            await player.skip()

            embed = Embed(title="Track Skipped", description='Skipped the current track.', color=discord.Color.orange())
            await ctx.send(embed=embed)
        except Exception as e:
            embed = Embed(title="Error", description=f"An error occurred while trying to skip the track: {str(e)}", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command()
    @commands.check(create_player)
    async def volume(self, ctx, volume: int):
        try:
            player = self.bot.lavalink.player_manager.get(ctx.guild.id)
            await player.set_volume(volume)

            embed = Embed(title="Volume Changed", description=f'Set the volume to {volume}.', color=discord.Color.blurple())
            await ctx.send(embed=embed)
        except Exception as e:
            embed = Embed(title="Error", description=f"An error occurred while trying to set the volume: {str(e)}", color=discord.Color.red())
            await ctx.send(embed=embed)
            
    @commands.command()
    @commands.check(create_player)
    async def pause(self, ctx):
        try:
            player = self.bot.lavalink.player_manager.get(ctx.guild.id)
            await player.set_pause(True)

            embed = Embed(title="Paused", description="The music has been paused.", color=discord.Color.orange())
            await ctx.send(embed=embed)
        except Exception as e:
            embed = Embed(title="Error", description=f"An error occurred while trying to pause the music: {str(e)}", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command()
    @commands.check(create_player)
    async def resume(self, ctx):
        try:
            player = self.bot.lavalink.player_manager.get(ctx.guild.id)
            await player.set_pause(False)

            embed = Embed(title="Resumed", description="The music has been resumed.", color=discord.Color.green())
            await ctx.send(embed=embed)
        except Exception as e:
            embed = Embed(title="Error", description=f"An error occurred while trying to resume the music: {str(e)}", color=discord.Color.red())
            await ctx.send(embed=embed)

bot = MusicBot()
bot.run('MTE2ODg2NjI3MTA0NDA1MDk1Nw.GyzGtr.8-guWJiIeDprjlQ2kzFMJfzcx8WMLXYTKOZuNM')
