import discord
from datetime import datetime
from discord.ext import commands
from facebook_scraper import get_posts
from sqlite3 import IntegrityError
import concurrent.futures


# CUSTOM ERRORS

# Raised when inputted streamer does not exist in database
class StreamerDoesntExist(commands.CommandError):
    pass

#Raised when inputted streamer is already in database
class StreamerAlreadyImplemented(commands.CommandError):
    pass

#Raised when Streamer cannot be located
class StreamerNotFound(commands.CommandError):
    pass


class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    async def cog_command_error(self, ctx, error):

        # Gets original attribute of error
        error = getattr(error, "original", error)

        if isinstance(error, StreamerDoesntExist):
            await ctx.send("That Streamer is not in the database!")

        elif isinstance(error, StreamerNotFound):
            await ctx.send("Could not find streamer. Are you sure you typed the username correctly?")

        elif isinstance(error, StreamerAlreadyImplemented):
            await ctx.send("That Streamer is already in the database!")


    def validateUsername(self, username : str) -> bool:

        try:

            for _ in get_posts(username, pages=1, cookies=self.bot.COOKIES_PATH):
                break

        except Exception as e:
            print(e)
            return False

        else:
            return True


    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name='add',description='Command to add streamer', aliases=['a'])
    async def add(self, ctx, user : str, channel : discord.TextChannel):

        await ctx.trigger_typing()

        username = user.lower()


        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await self.bot.loop.run_in_executor(pool, self.validateUsername, username)

        if not result:
            raise StreamerNotFound


        sql = 'INSERT INTO streamers(username) VALUES (?)'
        sql2 = 'UPDATE streamers set channel = ? where username = ?'

        try:
            await self.bot.db.execute(sql, (username,))
            await self.bot.db.execute(sql2, (channel.id, username))
            await self.bot.db.commit()


        except IntegrityError:
            raise StreamerAlreadyImplemented

        else:
            self.bot.streamers[username] = channel

            embed = discord.Embed(
                title="Action Successful",
                description=f"Streamer Added: {user}",
                colour=discord.Colour.green()
            )

            embed.add_field(name="Announcement Channel", value=channel.mention)

            return await ctx.send(embed=embed)




    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name='remove',description='Command to remove streamer',aliases=['r'])
    async def remove(self, ctx, user : str):


        username = user.lower()

        if username not in self.bot.streamers:
            raise StreamerDoesntExist


        sql = 'DELETE FROM streamers WHERE username=?'

        async with self.bot.db.execute(sql, (username,)) as cursor:
            await self.bot.db.commit()

        del self.bot.streamers[username]

        embed = discord.Embed(
            title="Action Successful",
            description=f"Streamer Removed: {user}",
            colour=discord.Colour.red()
        )

        await ctx.send(embed=embed)


    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name='list', description='Command that lists all Streamers being Monitored', aliases=['lst','l', 'ls'])
    async def list(self, ctx):

        streamers = self.bot.streamers.keys()

        if len(streamers) == 0:
            return await ctx.send("There are currently no Streamers being monitored. Add them via the `add` command")

        mapped = '\n'.join(map(str,streamers))

        embed = discord.Embed(
            title="List of Streamers currently being Monitored",
            description=f"`{mapped}`",
            colour=discord.Colour.blue(),
            timestamp=datetime.utcnow()
        )

        embed.set_footer(text=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url)

        return await ctx.send(embed=embed)




#Setup
def setup(bot):
    bot.add_cog(Commands(bot))