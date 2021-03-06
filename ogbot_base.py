import asyncio
import datetime
import inspect
import itertools
import platform

import colorama
import discord
import psutil
from colorama import Fore
from discord.ext import commands


class OGBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        intents = discord.Intents.all()
        self.dt_start = None
        command_prefix = kwargs.pop('command_prefix', commands.when_mentioned_or('.'))
        super().__init__(command_prefix=command_prefix, intents=intents, *args, **kwargs)
        colorama.init()
        self.bot_proc = psutil.Process()
        self.game = ""
        self.gop_text_cd = 0
        self.gop_voice_cd = 0
        self.in_tmux = False
        self.debug = False
        # self.debug = True
        self._game_running = asyncio.Event(loop=self.loop)
        self._game_stopped = asyncio.Event(loop=self.loop)

        if platform.system() == "Linux":
            asyncio.get_child_watcher().attach_loop(self.loop)

    async def wait_until_ready(self, delay=0):
        await discord.Client.wait_until_ready(self)
        if delay:
            await asyncio.sleep(delay)

    async def wait_until_game_running(self, delay=0):
        await self._game_running.wait()
        if delay:
            await asyncio.sleep(delay)

    async def wait_until_game_stopped(self, delay=0):
        await self._game_stopped.wait()
        if delay:
            await asyncio.sleep(delay)

    async def set_bot_status(self, line1: str, line2: str, line3: str):
        padder = [line1.replace(' ', '\u00a0'), ''.join(list(itertools.repeat('\u3000', 40 - len(line1))))
                  + line2.replace(' ', '\u00a0'), ''.join(list(itertools.repeat('\u3000', 40 - len(line2))))
                  + line3.replace(' ', '\u00a0')]
        await self.change_presence(activity=discord.Game(f"{' '.join(padder)}"))

    async def get_loaded_cogs(self):
        return self.cogs

    @property
    def is_game_running(self):
        return self._game_running.is_set()

    @property
    def is_game_stopped(self):
        return self._game_stopped.is_set()

    # TODO: REWRITE THIS GARBAGE
    def bprint(self, text: str = '', *args):
        cur_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = text.split("\n")
        for line in lines:
            if self.debug:
                print(f"{cur_time} {inspect.stack()[1][3]} ~ {line}", *args)

            else:
                print(f"{Fore.LIGHTYELLOW_EX}{cur_time}{Fore.RESET} ~ {line}", *args)

    def run(self, token, start_time=datetime.datetime.now()):
        self.dt_start = start_time
        super().run(token)
