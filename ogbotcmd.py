import asyncio
import cmd
import datetime
import inspect
import os
import time
from collections import defaultdict
from pprint import pprint

from colorama import Fore

from utils.helpers import MiniChannel


# noinspection PyUnusedLocal,PyUnusedLocal
class OGBotCmd(cmd.Cmd):
    __slots__ = {'bot', 'loop', 'completekey', 'attributes', 'vars', 'methods'}

    def __init__(self, loop, bot):
        super().__init__(self)
        self.returns = []
        self.bot = bot
        self.loop = loop
        self.completekey = 'tab'
        self.attributes = [attr for attr in dir(self.bot) if not attr.startswith("__")]
        self.vars = [attr for attr in dir(self.bot) if
                     not callable(getattr(self.bot, attr)) and not attr.startswith("__")]
        self.methods = [attr for attr in dir(self.bot) if
                        callable(getattr(self.bot, attr)) and not attr.startswith("__")]
        self.prompt = f"{Fore.BLUE}{self.bot.user.name} >>>{Fore.RESET}"

    def default(self, line):
        self.do_exec(line)

    # noinspection PyUnusedLocal
    def do_status(self, line):
        """Prints name, uptime, loaded cogs, etc. of the bot."""
        uptime = datetime.datetime.utcnow() - self.bot.uptime
        print(f"""Name: {self.bot.user.name}
Uptime: {str(uptime)}
Loaded cogs: {", ".join(self.bot.cogs.keys())}""")

    def do_reload_cog(self, line):
        """Reloads a module."""
        folder = self.bot.cog_folder
        try:
            if line.find(".") == -1:
                self.bot.unload_extension("{}.{}".format(folder, line))
                self.bot.load_extension("{}.{}".format(folder, line))
            else:
                self.bot.unload_extension(line)
                self.bot.load_extension(line)
        except Exception as e:
            self.bot.bprint('\N{PISTOL}')
            self.bot.bprint('{}: {}'.format(type(e).__name__, e))
        else:
            self.bot.bprint('\N{OK HAND SIGN}')

    def do_reload_all_cogs(self, line):
        """Reloads all modules."""
        temp = self.bot.extensions.keys()
        for ex in temp:
            self.bot.unload_extension(ex)
            self.bot.load_extension(ex)
            pass

    def do_methods(self, line):
        """Prints all (non-private) methods in self.bot (any defined in ogbot_base or its superclasses)"""
        pprint(self.methods)

    def do_tasks(self, line):
        """Prints aio tasks launched by the user's code.

        If 'debug' is appended to this, the command will print all aio tasks.
        """

        try:
            x = asyncio.all_tasks(self.loop)
            suu = [(c._coro.__name__, c.get_stack()) for c in x]
            print("List of running tasks:")
            for x in suu:
                name, path = x[0], x[1]
                path = inspect.getabsfile(path[0])
                if os.getcwd().lower() in path.lower():
                    file = path.split('\\')[-1]
                    print(f" {name} ({file})")
                elif "debug" in line:
                    print(f" {name} (internal)")

        except AttributeError:
            x = asyncio.Task.all_tasks(self.loop)
            pprint(x)
            print("I errored btw lol")

    def do_loop(self, line):
        """Prints limited information about the current asyncio event loop."""
        print(self.loop)

    def do_vars(self, line):
        """Prints all vars in self.bot"""
        pprint(self.vars)

    @staticmethod
    def do_debug_input(line):
        """Echos any command line input"""
        print(type(line))
        print(line)

    def do_get_user_info(self, line):
        """Prints information about a Discord user"""
        x = self.loop.create_task(
            self._exec_async(self.bot.fetch_user, parameters=[int(line)], callback=self._bad_practice))
        while not x.done():
            time.sleep(1)
        time.sleep(.5)
        z = self.returns.pop()
        data = """Name: {} | ID: {}
is_bot: {} | Avatar: {}""".format(z.name, z.id, z.bot, z.avatar_url)
        print(data)

    def do_exec(self, line):
        """Run methods and return their values, or get the values of variables"""

        try:
            b = line.split(' ')
            func = getattr(self.bot, b[0])
            if callable(func) and b[1:]:
                params = tuple(inspect.signature(func).parameters)
                x = ' '.join(b[1:]).split('|')
                print(f"with parameters {x}")
                if inspect.iscoroutinefunction(func):
                    self.loop.create_task(self._exec_async(func, parameters=x))
                else:
                    try:
                        result = func(*b[1:])
                        print(result) if result else False
                    except RuntimeWarning:
                        pass
                    except TypeError:
                        print(f"Method {b[0]} requires {len(params)} but {len(x)} were given")
                        print(params)
                    else:
                        print(result)
            elif callable(func) and not b[1:]:
                print(f"Calling {b[0]}()")
                if inspect.iscoroutinefunction(func):
                    print('e')

                    def mrsa(rslt):
                        print(rslt)

                    self.loop.create_task(self._exec_async(func, callback=mrsa))

                elif inspect.isgeneratorfunction(func):
                    nn = set()
                    ndic = defaultdict(lambda: [])
                    for z in func():
                        if z.name not in nn:
                            nn.add(z)
                            # pp = ndic.get(z.cog.name).append(z)

                    nn = list(nn)
                    print(nn)
                    nn.sort(key=lambda x: x.cog.qualified_name if x.cog else "help")
                    for x in nn:
                        print(x)

                else:
                    try:
                        result = func()
                        print(result) if result else False
                    except RuntimeWarning:
                        pass
                    except TypeError:
                        params = tuple(inspect.signature(func).parameters)
                        print(f"Method {b[0]} requires {len(params)} but {len(b[1:])} were given")
                        print([params])

            else:
                if func is None:
                    print(f"Var {b[0]}: None")
                else:
                    print(f"Var {b[0]}:")
                    pprint(func)
        except Exception as e:
            print(e)

    def do_get_next_message(self, line):
        self.loop.create_task(self._exec_async(self.get_next_message_async))

    async def get_next_message_async(self):
        m = await self.bot.wait_for('message', timeout=60)
        vaas = f"""{m.author.name}({m.author.id})
-----Content-----
{Fore.GREEN}{m.clean_content}{Fore.RESET}
Channel: {MiniChannel(m.channel).name} ({m.channel.id})
Sent on {m.created_at.strftime('%a, %b %d, %Y at %I:%M:%S %p')}"""
        print(vaas)

    def complete_exec(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in self.attributes if s.startswith(mline)]

    def completedefault(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in self.attributes if s.startswith(mline)]

    def do_list_commands(self, line):
        # for x in self.bot.commands:
        #     print(x.qualified_name)
        #     print(self.bot.cogs)
        for name, cog in self.bot.cogs.items():
            # pprint(dir(cog))
            print("Module: " + name)
            for group in cog.get_commands():
                try:
                    assert group.commands
                    print("  | Group: " + str(group.qualified_name))
                    print("  +-------|")
                    for sc in group.commands:
                        print("          | " + sc.name)
                except AttributeError as e:
                    print("  | Command: " + str(group.qualified_name))
                    continue
                except Exception as e:
                    print(e.__class__)
                    print(dir(e))

    @staticmethod
    async def _exec_async(method, parameters=None, callback=None):
        try:
            if parameters:
                result = await asyncio.wait_for(method(*parameters), timeout=10)
            else:
                result = await asyncio.wait_for(method(), timeout=10)
            # print(result)
            if callback:
                callback(result)
        except Exception as e:
            print(e)

    def _bad_practice(self, result):
        self.returns.append(result)

    def do_set(self, line: str):
        """
        Set the value of a variable
        """

        x = line.split(" ", maxsplit=1)
        if len(x) is not 2:
            print("Please give a value to set the variable to.")
            return
        elif not hasattr(self.bot, x[0]):
            setattr(self.bot, x[0], x[1])
            print(f"Added attribute {x[0]} to {x[1]}")
            return
        else:
            var = getattr(self.bot, x[0])
            if isinstance(var, str):
                setattr(self.bot, x[0], str(x[1]))
            elif isinstance(var, int):
                setattr(self.bot, x[0], int(x[1]))
            elif isinstance(var, list):
                var = x[1].split(',')
                setattr(self.bot, x[0], var)

            else:
                print(f'Your variable typing is too strong! (Variable of type {type(var)} couldn\'t be processed)')

    def complete_set(self, text, line):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in self.vars if s.startswith(mline)]

    @staticmethod
    def do_exit(line):
        return True

    @staticmethod
    def do_stop(line):
        return True

    def cmdloop(self, intro=None):
        try:
            asyncio.set_event_loop(self.loop)
            super().cmdloop(intro=intro)
        finally:
            self.loop.stop()

    async def start(self):
        try:
            await self.loop.run_in_executor(None, self.cmdloop)
        except asyncio.CancelledError:
            pass
