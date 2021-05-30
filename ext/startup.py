import discord
import os
from discord.ext import commands
import aiosqlite

class Startup(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.initializeDB())


    async def updateStreamers(self):

        async with self.bot.db.execute("SELECT username FROM streamers") as cursor:
            rows = await cursor.fetchall()

            try:
                self.bot.streamers = [i[0] for i in rows]

            except IndexError:
                self.bot.streamers = list()


            print(self.bot.streamers)


    async def initializeDB(self):
        self.bot.db = await aiosqlite.connect('streamers.db')

        sql = """CREATE TABLE IF NOT EXISTS streamers (
            username TEXT PRIMARY KEY)
        """

        await self.bot.db.execute(sql)
        await self.bot.db.commit()

        await self.updateStreamers()



    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user.name} | {self.bot.user.id}')




#Setup
def setup(bot):
    bot.add_cog(Startup(bot))

