import asyncio
import json
import os
import random
import sqlite3

import discord
from discord.ext import commands

from utils import helpers


class Santa(commands.Cog):
    """Ho ho ho you're a ho."""

    def __init__(self, bot):
        self.bot = bot
        self.hohoholy_blessings = asyncio.Lock()
        # self.santa_channel = self.bot.get_channel('')

    @helpers.is_human()
    @commands.Cog.listener()
    async def on_add_reaction(self, reaction, author):
        await self.bot.wait_until_ready()
        # if message.channel.id == self.santa_channel.id and reaction.emoji == '\N{OK HAND SIGN}':
        #     if message.clean_content[0] != '#' and message.clean_content[0] != '>':
        #         await self.auto_comrade_check(message)
        # await self.auto_thonk(message)

    @commands.command()
    async def secret(self, ctx):
        """Find out who your secret elf buddy is for this year"""
        async with self.hohoholy_blessings:
            instant = True
            if os.path.exists('borderlands_the_pre.sql'):
                instant = False
            conn = sqlite3.connect('borderlands_the_pre.sql')
            cursor = conn.cursor()

            if ctx.author.id == self.bot.owner_id:
                # if table does not exist -> create it
                if instant:
                    conn.execute(
                        "create table santa(user_id, user_name, gifter_id, gifter_name, giftee_id, giftee_name)")

                with open("modules/ogbox.json") as sec:
                    lookup = json.load(sec)
                    people = list()
                    for x, y in lookup.items():
                        people.append(x)

                continue_go = True
                while continue_go:
                    random.shuffle(people)
                    for x in range(len(people)):
                        g, r = x % len(people), (x + 1) % len(people)
                        if 'Evan' in (people[g], people[r]) and 'Zach' in (people[g], people[r]):
                            break
                    else:
                        break

                cursor.execute('delete from santa')

                for x, person in enumerate(people):
                    b, g, a = (x - 1) % len(people), x % len(people), (x + 1) % len(people)
                    the_world = (
                        lookup[people[b]], people[b], lookup[people[g]], people[g], lookup[people[a]], people[a])
                    cursor.execute('insert into santa VALUES (?, ?, ?, ?, ?, ?)', the_world)
                conn.commit()

                for x, person in enumerate(people):
                    discord_id = lookup[person]
                    gifter = person.capitalize()
                    giftee = people[(x + 1) % len(people)].capitalize()
                    message = """
{}, you have been assigned {}'s secret santa.
If you'd like to ask them their shirt size, shoe size, favorite color, ideal date location, a/s/l (okay maybe not those last two...) use `>ask` 
To ask everyone in the group the above, use `>askall`
If your asks you a question, and you want to respond, use `>respond`
It's recommended that you go invisible on Discord when you send `>ask` questions, since I can't prevent people from puzzling that out.

Recommended price limit: ~$30
Secret Santa gifts can be silly or serious.
Example: For Xmas 2018, Brandon got an autism shirt, Zach got a unicorn plush, and Aero got a DIY shelf for his stuff.

Please try not to give away who you are to your secret santa, as that ruins the fun of the event.
Misleading your secret santa and giving them a different one is allowed & encouraged.
""".format(gifter, giftee)
                    # member = self.bot.get_user(141752316188426241)
                    member = self.bot.get_user(discord_id)
                    await member.send(content=message)
            else:
                try:
                    # get stuff from sql db
                    pass
                except:
                    # Raise NotASecretSantaError
                    pass

    @commands.command()
    async def ask(self, ctx):
        async with self.hohoholy_blessings:
            conn = sqlite3.connect('borderlands_the_pre.sql')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM santa WHERE user_id=?', (ctx.author.id,))
            u_id, u_name, _, _, g_id, g_name = cursor.fetchone()

            member = self.bot.get_user(int(g_id))
            msg = "From your gifter:\n {}".format(ctx.message.clean_content.lstrip(str(ctx.prefix) + str(ctx.command)))

            await member.send(content=msg)

    @commands.command()
    async def respond(self, ctx):
        async with self.hohoholy_blessings:
            conn = sqlite3.connect('borderlands_the_pre.sql')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM santa WHERE user_id=?', (ctx.author.id,))
            u_id, u_name, g_id, g_name, _, _ = cursor.fetchone()

            member = self.bot.get_user(int(g_id))
            msg = "From your giftee, {}:\n {}".format(u_name, ctx.message.clean_content.lstrip(
                str(ctx.prefix) + str(ctx.command)))
            await member.send(content=msg)

    @commands.command(aliases=['question', 'poll'])
    async def anonquestion(self, ctx):
        await ctx.send(
            'Now creating an anonymized question.\nPlease try to keep a professional tone.\nRespond with your question.')
        while True:
            e = discord.Embed(color=discord.Color.green())
            e.set_author(name="Someone asked...")
            try:
                val = (await self._get_next_message(ctx)).clean_content.lstrip(str(ctx.prefix) + str(ctx.command))
            except TimeoutError:
                await ctx.send('Timed out. Please send the `>anonquestion` command again to write a question.')
                break
            e.description = val
            preview = await self.send_with_yes_no_reactions(ctx,
                                                            message='This is how your question will look. Are you sure you want to send this message?',
                                                            embed=e)
            try:
                reaction = await self.get_yes_no_reaction(preview)
                if reaction:
                    await ctx.send('Okay, sending...')
                    # SEND TO QUESTION CHANNEL
                    await ctx.send(embed=e)
                    break
                else:
                    await ctx.send('Okay, please type your question again.')
            except asyncio.TimeoutError:
                await ctx.send('Timed out. Please send the `>anonquestion` command again to write a question.')
                break
            except asyncio.CancelledError:
                await ctx.send('Okay, canceled question creation.')
                break

    async def _get_next_message(self, ctx) -> discord.Message:
        msg = await self.bot.wait_for('message', timeout=120.0,
                                      check=lambda message: message.channel == ctx.channel and isinstance(
                                          ctx.channel, discord.DMChannel))
        return msg

    async def send_with_yes_no_reactions(self, ctx, message: str = '', embed: discord.Embed = None):
        reactions = ('\N{THUMBS UP SIGN}', '\N{THUMBS DOWN SIGN}', '\N{CROSS MARK}')

        if message and embed:
            msg = await ctx.send(message, embed=embed)
        elif embed:
            msg = await ctx.send(embed=embed)
        else:
            msg = await ctx.send(message)

        try:
            [await x for x in [msg.add_reaction(reaction) for reaction in reactions]]

        except Exception as e:
            print('{}: {}'.format(type(e).__name__, e))
            await self.bot.bprint('{}: {}'.format(type(e).__name__, e))
            await self.bot.get_user(self.bot.owner_id).send('{}: {}'.format(type(e).__name__, e))
            # ^^ This line is garbage, refactor this.
            await ctx.send('Something went wrong. Evan has been notified.')

        return msg

    async def get_yes_no_reaction(self, ctx, message: discord.Message = None, timeout=120.0):
        def same_channel(reaction, user):
            if message:
                return ctx.author == user and reaction.message.channel == ctx.channel and reaction.message == message
            else:
                return ctx.author == user and reaction.message.channel == ctx.channel

        reaction, author = await self.bot.wait_for('reaction_add', timeout=timeout, check=same_channel)

        if reaction.emoji == '\N{THUMBS UP SIGN}':
            return True
        elif reaction.emoji == '\N{THUMBS DOWN SIGN}':
            return False
        elif reaction.emoji == '\N{CROSS MARK}':
            raise asyncio.CancelledError

    @commands.command()
    async def get_reaction(self, ctx):
        def check(_, user):
            return ctx.author == user

        pp = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
        print('{}: {} --- {}'.format(type(pp).__name__, pp, pp[0].emoji))
        await ctx.send('{}: {}'.format(type(pp).__name__, pp))

    # @commands.command()
    # async def r(self, ctx):
    #     print(ctx.message.clean_content.lstrip(str(ctx.prefix) + str(ctx.command)))
    #     print(ctx.message.content.lstrip(str(ctx.prefix) + str(ctx.command)))
    #     print('\N{PISTOL}')
    #

    # Real Numbers
    # {
    #     "Evan": 141752316188426241,
    #     "Brandon": 146777902501855232,
    #     "Steven": 155794959365046273,
    #     "David": 158704434954764288,
    #     "Zach": 159388909346750465,
    #     "Aero": 239192698836221952,
    #     "Jeromie": 249639501004144640,
    #     "CJ": 530099291478556701
    # }

    # Fake Numbers for testing
    # {
    #     "Evan": 141752316188426241,
    #     "Brandon": 141752316188426241,
    #     "Steven": 141752316188426241,
    #     "David": 141752316188426241,
    #     "Zach": 141752316188426241,
    #     "Aero": 141752316188426241,
    #     "Jeromie": 141752316188426241,
    #     "CJ": 141752316188426241
    # }


# Okay, I guess I'll do any further updates on the bot in here:
# ~ People will be able to ask questions to the entire group anonymously, and everyone will be required to participate.
#  Everyone will also be able to see everyone else's answers.
# ~ Questions to be answered will show up in a channel in this server.
# ~ You will be able to click a reaction button to give a response via DM's (This is for keeping the channel clean, everyone who responds will have their name given.)


def setup(bot):
    bot.add_cog(Santa(bot))
