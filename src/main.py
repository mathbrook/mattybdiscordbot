import discord
from discord.ext import tasks, commands
import requests
import json
import os
import logging
import random
import pylast

logging.basicConfig(level=logging.INFO)

def load_creds(creds_json_path=r"bot_creds.json"):
    with open(creds_json_path, "r") as credsfile:
        creds = json.load(credsfile)
        return creds

def load_bot_token():
    creds = load_creds()
    return creds["discord_credentials"]["bot_token"]

def get_channel_by_criteria(guild):
    # Get a list of all text channels
    text_channels = [
        channel
        for channel in guild.channels
        if isinstance(channel, discord.TextChannel)
    ]

    # Sort by alphabetical order (or numerical order if using channel IDs)
    sorted_channels = sorted(
        text_channels, key=lambda ch: ch.name
    )  # By name (alphabetical)
    # sorted_channels = sorted(text_channels, key=lambda ch: ch.id)  # By ID (numerical)

    return sorted_channels[0] if sorted_channels else None


class MathbrookMusicReporter:
    def __init__(self, creds=load_creds()):
        creds = creds["lastfm_credentials"]
        self.__username = creds["username"]
        self.__password = pylast.md5(creds["password"])
        self.__apikey = creds["api_key"]
        self.__shared_secret = creds["shared_secret"]
        self.lastfmclient = pylast.LastFMNetwork(
            api_key=self.__apikey,
            api_secret=self.__shared_secret,
            username=self.__username,
            password_hash=self.__password,
        )
        self.lastfmclient.enable_rate_limit()
        # Attempt to get user pfp on init
        self.__mathbrook_pfp = self.user.get_image(size=pylast.SIZE_MEDIUM)
        logging.info(f"Init success? Mathbrook pfp url: {self.__mathbrook_pfp}")

    @property
    def user(self) -> pylast.User:
        return self.lastfmclient.get_user(self.__username)

    @property
    def pfp(self) -> str:
        return self.__mathbrook_pfp

    def current_song(self) -> pylast.Track | pylast.PlayedTrack:
        song = self.user.get_now_playing()
        if song is None:
            song = self.user.get_recent_tracks(limit=1)[0]
        return song


description = """An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here."""

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
logging.info("here")
# bot = commands.Bot(command_prefix="?", description=description, intents=intents)

lastfmclient = MathbrookMusicReporter()


class MathbrookBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="?", description=description, intents=intents)
        self.last_listened = ""
        self.pfp_filename = ""


bot = MathbrookBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    listening_announcement.start()
    change_profile_picture.start()

@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    embed = discord.Embed(
        title="Addition", description="added two numbers!", color=0xFFFFFF
    )
    embed.add_field(name="result", value=(left + right))
    await ctx.send(embed=embed)


@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f"{member.name} joined {discord.utils.format_dt(member.joined_at)}")


def get_mathbrook_listening_msg():
    song = lastfmclient.current_song()
    embed = discord.Embed(
        title="Mathbrook's current jam!",
        color=random.randint(0, 0xFFFFFF),
        
    )
    msg = ""
    song_name = ""
    artist = None
    album = ""
    if isinstance(song, pylast.PlayedTrack):
        msg = f"Mathbrook is listening to: {song.track} from {song.album}"
        embed.add_field(name="Song", value=song.track)
        embed.add_field(name="Album", value=song.album)
    elif isinstance(song, pylast.Track):
        embed.add_field(name="Song", value=(song.title))
        embed.add_field(name="Album", value=(song.get_album().title))
        embed.add_field(name="Artist", value=(song.artist))
        embed.set_image(url=song.get_cover_image(pylast.SIZE_EXTRA_LARGE))
        msg = f"Mathbrook is listening to: {song.title} from {song.get_album().title}, by {song.artist}"
        embed.set_footer(text = f"scrobbles of this track: {song.get_userplaycount()} total scrobbles: {lastfmclient.user.get_playcount()}")
    embed.set_thumbnail(url=lastfmclient.pfp)
    return msg, embed


@bot.command()
async def np(ctx: discord.TextChannel):
    """Returns what mathbrook is currently listening to on lastfm"""
    msg, embed = get_mathbrook_listening_msg()
    await ctx.send(content=msg, embed=embed)


@tasks.loop(seconds=30)
async def listening_announcement():
    channel = bot.get_channel(
        int(load_creds()["discord_credentials"]["test_channel_id"])
    )  # Hard coded bot channel ID in my server
    assert(channel is not None)
    msg, embed = get_mathbrook_listening_msg()
    logging.info(f"Auto song post got {msg} {embed}")
    logging.info(f"Bot last listened is currently: {bot.last_listened}")
    if bot.last_listened != msg:
        logging.info(f"This is a new song")
        bot.last_listened = msg
        if channel is not None:
            logging.info(f"Sending!")
            await channel.send(content=msg, embed=embed)

def embed_avatar(ctx: discord.TextChannel, member: discord.Member = None):
    member = member or ctx.author  # Default to the command invoker if no member is mentioned

    # Create an embed
    embed = discord.Embed(
        title=f"{member.display_name}'s Avatar",
        color=discord.Color.blue()
    )
    embed.set_image(url=member.avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
    return embed

@bot.command()
async def user_avatar(ctx, member: discord.Member = None):
    """Sends an embed with a user's avatar."""
    embed = embed_avatar(ctx=ctx, member=member)
    # Send the embed
    await ctx.send(embed=embed)

@bot.command()
async def bot_avatar(ctx):
    embed = embed_avatar(ctx=ctx, member=bot.user)
    embed.set_footer(text=f"{embed.footer.text}, filename: {bot.pfp_filename[:10]}...", icon_url=embed.footer.icon_url)
    await ctx.send(embed=embed)

@bot.command()
async def changeavatar(ctx, url=None):
    """Make the bot change its avatar, optionally using a URL."""
    image = await changepfp(url)
    await ctx.send(content="Changed pfp!")

async def changepfp(url=None):
    """Change the bot's profile picture to a random image or from a URL."""
    if url:
        # Handle the URL case
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for HTTP issues

            image_data = response.content

            # Try updating the bot's profile picture
            await bot.user.edit(avatar=image_data)
            print("Profile picture updated successfully from URL!")
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch image from URL: {e}")
        except discord.HTTPException as e:
            print(f"Failed to update profile picture: {e}")
    else:
        # Handle the random selection from directory case
        image_directory = "../assets/avatars/"

        # List all files in the directory
        image_files = [f for f in os.listdir(image_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

        if not image_files:
            print("No valid image files found in the specified directory.")
            return

        # Choose a random image file
        random_image = random.choice(image_files)
        image_path = os.path.join(image_directory, random_image)

        # Read the selected image file
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        # Try updating the bot's profile picture
        try:
            await bot.user.edit(avatar=image_data)
            print(f"Profile picture updated successfully to {random_image}!")
            bot.pfp_filename = random_image 
        except discord.HTTPException as e:
            print(f"Failed to update profile picture: {e}")

@tasks.loop(minutes=60)
async def change_profile_picture():
    await changepfp()

bot.run(load_bot_token())
