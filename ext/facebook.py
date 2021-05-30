import discord
import os
import concurrent.futures
from facebook_scraper import get_posts
from discord.ext import commands, tasks

class Facebook(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.announced = list()
        self.check_if_live.start()


    def makeRequests(self, username):
        #print(username)

        for post in get_posts(username, pages=1):
            #print(post)

            if post['is_live']:
                return (username, post['user_url'], post['username'])

        return False



    @tasks.loop(seconds=600)
    async def check_if_live(self):

        streamers = self.bot.streamers

        if len(self.bot.streamers) == 0:
            return

        for username in streamers:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = await self.bot.loop.run_in_executor(pool, self.makeRequests, username)

            # If Live Stream is finished for particular user
            if not result and username in self.announced:
                self.announced.remove(username)

            #If Live Stream is still going for particular user but has already been announced
            elif result and username in self.announced:
                continue

            #If Live Stream is going for particular user and has not been announced
            elif result and username not in self.announced:
                username, url, user = result

                channel = self.bot.get_channel(int(os.environ["ANNOUNCEMENT-CHANNEL"]))
                await channel.send(f" @everyone {user} is live at {url}. Go check it out!")
                self.announced.append(username)

            else:
                continue


    @check_if_live.before_loop
    async def before_live_check(self):
        await self.bot.wait_until_ready()




#Setup
def setup(bot):
    bot.add_cog(Facebook(bot))