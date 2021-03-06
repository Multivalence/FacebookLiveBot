import discord
import os
import asyncio
import concurrent.futures
from facebook_scraper import get_posts
from discord.ext import commands, tasks

class FacebookLive(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.announced = list()
        self.check_if_live.start()

        #Time is in seconds
        self.WAIT_TIME = 120



    def makeRequests(self, username):

        for post in get_posts(username, pages=2, cookies=self.bot.COOKIES_PATH):

            if post['is_live']:
                return (username, post)

        return False



    @tasks.loop(seconds=600)
    async def check_if_live(self):

        streamers = self.bot.streamers.copy()

        if len(set(self.bot.streamers.keys())) == 0:
            return

        for username in streamers:

            await asyncio.sleep(self.WAIT_TIME)

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
                username, post = result

                channel = streamers[username]

                embed = discord.Embed(
                    title=f"New Livestream by {post['username']}",
                    description=f"[Livestream Link]({post['user_url']})",
                    colour=discord.Colour.gold(),
                    timestamp=post['time']
                )

                embed.add_field(name="\u200b", value=post['post_text'])

                if post["image_lowquality"]:
                    embed.set_image(url=post["image_lowquality"])


                elif post["video"]:
                    embed.set_image(url=post["video_thumbnail"])


                await channel.send(embed=embed)
                self.announced.append(username)

            else:
                continue


    @check_if_live.before_loop
    async def before_live_check(self):
        await self.bot.wait_until_ready()




#Setup
def setup(bot):
    bot.add_cog(FacebookLive(bot))
