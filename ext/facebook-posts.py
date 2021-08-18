import aiohttp
import discord
import os
import asyncio
import concurrent.futures
from discord import Webhook, AsyncWebhookAdapter
from facebook_scraper import get_posts
from datetime import datetime, timedelta
from discord.ext import commands, tasks



class FacebookPosts(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.channel_name = "TheMilianaire"
        self.announced = list()
        self.date = datetime.today().strftime("%Y-%m-%d")

        self.bot.loop.create_task(self.identifyWebhook())

        self.check_posts.start()
        self.update_date.start()



    async def identifyWebhook(self):

        await self.bot.wait_until_ready()

        channel = self.bot.get_channel(int(os.environ["POST-CHANNEL"]))
        whooks = await channel.guild.webhooks()


        for i in whooks:
            if i.name == "Facebook Posts":
                self.url = i.url
                return


        async with aiohttp.ClientSession() as cs:
            async with cs.get(str(self.bot.user.avatar_url)) as r:
                image_bytes = await r.read()

            web = await channel.create_webhook(name="Facebook Posts", avatar=image_bytes, reason="Logging Facebook Posts")

            self.url = web.url
            return





    def generate_embed(self):

        embeds = []

        # cookies=self.bot.COOKIES_PATH
        for post in get_posts(self.channel_name, pages=2, cookies=self.bot.COOKIES_PATH):

            post_date = post['time'].strftime("%Y-%m-%d")

            if post['post_id'] in self.announced:
                continue

            if post_date != self.date:
                continue


            embed = discord.Embed(
                title=f"Fb.com/{self.channel_name}",
                description=f"[Post Link]({post['post_url']})",
                colour=discord.Colour.green(),
                timestamp=post['time']
            )

            embed.add_field(name="\u200b", value=post['post_text'])

            if post["image_lowquality"]:
                embed.set_image(url=post["image_lowquality"])


            elif post["video"]:
                embed.add_field(name="\u200b", value=f"[Video Link]({post['video']})")
                embed.set_image(url=post["video_thumbnail"])

            self.announced.append(post['post_id'])

            embeds.append(embed)

        return reversed(embeds)




    @tasks.loop(seconds=600)
    async def check_posts(self):

        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await self.bot.loop.run_in_executor(pool, self.generate_embed)

        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(self.url, adapter=AsyncWebhookAdapter(session))

            for embed in result:
                await webhook.send(embed=embed)



    @tasks.loop(seconds=5)
    async def update_date(self):

        today = datetime.today().strftime("%Y-%m-%d")

        if datetime.strptime(today, "%Y-%m-%d") == datetime.strptime(self.date, "%Y-%m-%d") + timedelta(days=1):
            self.announced = []

        self.date = today



    @check_posts.before_loop
    async def before_post_check(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(300)





#Setup
def setup(bot):
    bot.add_cog(FacebookPosts(bot))
