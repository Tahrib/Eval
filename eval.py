import discord
from discord.ext import commands
import urllib.parse, urllib.request, re
from contextlib import redirect_stdout
import asyncio
from datetime import datetime, timedelta
import ast
import inspect
import io
import textwrap
import traceback
import aiohttp
import time
import random
import asyncpg



"""Evaluate Python commands directly from discord. Please note this command can be very dangerous if abused
so to protect your computer and your discord server we've limited this command to the bot owner only.
Credits goes to @tahribtajwarmusic, for any queries please contact me on Discord.
REQUIREMENTS:
discord.py 2.3.0 or higher
"""


class eval(commands.Cog):
    
    def __init__(self, client):
        
        self.bot = client

        self.pool = client.pool
        


    @commands.Cog.listener()
    async def on_ready(self):

        """Bot startup"""

        print("Eval cog loaded!")
        

    
    @commands.command(name='eval', aliases=["e", "ev"])
    @commands.is_owner()
    async def _eval(self, ctx, *, body):

        """Evaluates python code"""
        env = {
            
            'self': self,

            'client': self.bot,

            'ctx': ctx,

            'bot': self.bot,

            'channel': ctx.channel,

            'author': ctx.author,

            'guild': ctx.guild,

            'message': ctx.message,

            'source': inspect.getsource

        }

        def cleanup_code(content):

            """Automatically removes code blocks from the code."""

            # remove ```py\n```

            if content.startswith('```') and content.endswith('```'):
                return content.strip("```")

            # remove `foo`

            return content.strip('` \n')

        def get_syntax_error(e):

            if e.text is None:

                return f'```py\n{e.__class__.__name__}: {e}\n```'

            return f'{ctx.author.mention} \u274c Your eval job has completed with return code 1.\n\n```py\n{traceback.format_exc()}\n```'

        env.update(globals())

        body = cleanup_code(body)

        stdout = io.StringIO()

        err = out = None

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        def paginate(text: str):

            '''Simple generator that paginates text.'''

            last = 0

            pages = []

            for curr in range(0, len(text)):

                if curr % 1980 == 0:

                    pages.append(text[last:curr])

                    last = curr

                    appd_index = curr

            if appd_index != len(text)-1:

                pages.append(text[last:curr])

            return list(filter(lambda a: a != '', pages))

        try:

            exec(to_compile, env)

        except Exception as e:

            err = await ctx.send(f'{ctx.author.mention} \u274c Your eval job has completed with return code 1.\n\n```py\n{traceback.format_exc()}\n```')

            await ctx.message.add_reaction("\u274c")

            await err.add_reaction("\u23f9")
            
            def check(reaction, user):

                return str(reaction.emoji) == "\u23f9" and reaction.message.id == err.id and user.id == ctx.author.id
            
            try:

                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            
            except asyncio.TimeoutError:

                await err.clear_reactions()

                return
            
            else:

                await err.delete()

                return

        func = env['func']

        try:

            with redirect_stdout(stdout):

                ret = await func()

        except Exception as e:

            value = stdout.getvalue()

            err = await ctx.send(f'{ctx.author.mention} \u274c Your eval job has completed with return code 1.\n\n```py\n{value}{traceback.format_exc()}\n```')

        else:

            value = stdout.getvalue()

            if ret is None:

                if value:

                    try:

                        out = await ctx.send(f'{ctx.author.mention} \u2705 Your eval job has completed with return code 0.\n\n```py\n{value}\n```')

                    except:

                        paginated_text = paginate(value)

                        for page in paginated_text:

                            if page == paginated_text[-1]:

                                out = await ctx.send(f'{ctx.author.mention} \u2705 Your eval job has completed with return code 0.\n\n```py\n{page}\n```')

                                break
                            

                            await ctx.send(f'{ctx.author.mention} \u2705 Your eval job has completed with return code 0.\n\n```py\n{page}\n```')

            else:

                try:

                    out = await ctx.send(f'{ctx.author.mention} \u2705 Your eval job has completed with return code 0.\n\n```py\n{value}{ret}\n```')

                except:

                    paginated_text = paginate(f"{value}{ret}")

                    for page in paginated_text:

                        if page == paginated_text[-1]:

                            out = await ctx.send(f'{ctx.author.mention} \u2705 Your eval job has completed with return code 0.\n\n```py\n{page}\n```')

                            break

                        await ctx.send(f'{ctx.author.mention} \u2705 Your eval job has completed with return code 0.\n\n```py\n{page}\n```')

        if out:
            await ctx.message.add_reaction('\u2705') 
            await out.add_reaction("\u23f9")

            def check(reaction, user):
                return str(reaction.emoji) == "\u23f9" and reaction.message.id == out.id and user.id == ctx.author.id

            try:

                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

            except asyncio.TimeoutError:

                await out.clear_reactions()

            else:

                await out.delete()

        elif err:

            await ctx.message.add_reaction('\u274c')  

            await err.add_reaction("\u23f9")

            def check(reaction, user):

                return str(reaction.emoji) == "\u23f9" and reaction.message.id == err.id and user.id == ctx.author.id

            try:

                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

            except asyncio.TimeoutError:

                await err.clear_reactions()

            else:

                await err.delete()

        else:

            await ctx.message.add_reaction('\u2705')  



    @_eval.error
    async def _eval_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.message.add_reaction('\u274c')  
            out = await ctx.send(f"{ctx.author.mention} \u274c Your eval job has completed with return code 1.\n\n```Py\ndiscord.ext.commands.errors.{error.__class__.__name__}: {error}\n```")
            await out.add_reaction("\u23f9")

            def check(reaction, user):
                return str(reaction.emoji) == "\u23f9" and reaction.message.id == out.id and user.id == ctx.author.id

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

            except asyncio.TimeoutError:
                await out.clear_reactions()

            else:
                await out.delete()
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.add_reaction('\u274c') 
            out = await ctx.send(f"{ctx.author.mention} \u274c Your eval job has completed with return code 1.\n\n```Py\ndiscord.ext.commands.errors.{error.__class__.__name__}: {error}\n```")
            await out.add_reaction("\u23f9")

            def check(reaction, user):
                return str(reaction.emoji) == "\u23f9" and reaction.message.id == out.id and user.id == ctx.author.id

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

            except asyncio.TimeoutError:
                await out.clear_reactions()

            else:
                await out.delete()
            

async def setup(client):
    await client.add_cog(eval(client))
