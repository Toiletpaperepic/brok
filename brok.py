from datetime import datetime
from enum import Enum
from typing import Optional
from openai import AsyncOpenAI
import requests
import discord
from discord import Colour, Embed, app_commands
from discord.ext import commands
# import random
import re
import os

openai_host = os.environ['OPENAI_HOST']
openai_key = os.environ['OPENAI_KEY']
MAIN_GUILD = discord.Object(id=os.environ['MAIN_GUILD'])
BOT_OWNER = int(os.environ['BOT_OWNER'])
BOT_CHANNEL_ID = int(os.environ['BOT_CHANNEL_ID'])

openaiapi = AsyncOpenAI(base_url=openai_host + "/v1", api_key=openai_key)

message_max_size = 2000

def websocket_log(content):
    payload = {'content': content}
    
    r = requests.post(client.webhook, data=payload)

def unload(model):
    if model.status["value"] == "loaded":
        data = {
            # 'Authorization': 'Bearer ' + openai_key, 
        }
        json = {
            'model': model.id
        }
            
        r = requests.post(openai_host + "/models/unload", data=data, json=json)
        # websocket_log("``" + r.text + "``")
        r.raise_for_status()
        websocket_log("unloaded: ``" + model.id + "``")
    else:
        websocket_log("Model is not running: ``" + model.id + "``")

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # self.tree.clear_commands(guild=None)
        # await self.tree.sync()
        # self.tree.copy_global_to(guild=MAIN_GUILD)
        # await self.tree.sync(guild=MAIN_GUILD)
        print("setup_hook() done.")

    async def generate_message(self, message, systemprompt):            
        print(systemprompt)

        reply_message = None if message.reference is None else (await message.channel.fetch_message(message.reference.message_id))

        listofmessages = [{"role": "system", "content": systemprompt}]
        if reply_message is not None:
            print("got a reply!")
            while reply_message is not None:
                listofmessages.append({"role": ("assistant" if reply_message.author == self.user else "user"), "content": reply_message.clean_content})
                reply_message = None if reply_message.reference is None else (await reply_message.channel.fetch_message(reply_message.reference.message_id))
            listofmessages.append({"role": "user", "content": message.clean_content})
        else:
            print("looking at channel history")
            messages_history = [message async for message in message.channel.history(limit=10)]
            for msg in messages_history:    
                # print(msg.author == self.user)
                listofmessages.insert(1, {"role": ("assistant" if msg.author == self.user else "user"), "content": msg.clean_content})

        print(listofmessages)
        
        response = await openaiapi.chat.completions.create(
            model=self.model_set,
            messages=listofmessages,
        )
        response = response.choices[0].message.content

        print(response)

        # regex_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        regex_response = re.sub(r'@(?=(?!\s)\w)|(?=<)@(?=(|&)\d*>)', '\\@', response, flags=re.DOTALL)

        # if regex_response is response:
        return regex_response

    async def on_ready(self):
        self.appinfo = await self.application_info()
        print(f'Logged on as {self.user}!')

        # if not hasattr(MyClient, 'appinfo'):

#     def create_system_prompt(self, message):
#         return """You are a helpful assistant.
# the time right now is """ + datetime.now().strftime('%A, %B %d, %Y %I:%M:%S %p') + """.
# in this online chatroom you are mentioned as \"<@""" + str(self.appinfo.id) + """>\".
# the next message is from """ + str(message.author) + """ (mentioned as: <@""" + str(message.author.id) + """>).
# play into the act that you are president obama that uses his ***Emergency Presidential*** stash of things,
# owns a mountain in colorado""" + (", use \"" + str(random.choice(message.guild.emojis)) + "\", \"" + str(random.choice(message.guild.emojis)) + "\", and \"" + str(random.choice(message.guild.emojis)) + "\" alot in your writing." if message.guild is not None else ".")

    def create_system_prompt(self, message):
        return """You are a helpful assistant. your gender is a women.
the time right now is """ + datetime.now().strftime('%A, %B %d, %Y %I:%M:%S %p') + """.
in this online chatroom you are mentioned as \"""" + str(self.appinfo.name) + """\" (you as in the helpful assistant that you are.).
the next message is from \"""" + str(message.author.nick if (message.author.nick is not None if hasattr(message.author, "nick") else False) else (message.author.global_name if message.author.global_name is not None else message.author.name)) + """\" (as in the user asking you a question.).
Please keep your response short!"""

    async def on_message(self, message):
        try:
            if message.author.bot or message.author == self.user or message.content == "":
                return

            print(f'Message from {message.author}: {message.content}')
            if (message.channel.type == discord.ChannelType.private or message.channel.id == BOT_CHANNEL_ID or self.appinfo.id in map(lambda s: s.id,message.mentions)):
                async with message.channel.typing():
                    response = await self.generate_message(message, self.create_system_prompt(message)) 

                    for x in [response[y-message_max_size:y] for y in range(message_max_size, len(response)+message_max_size,message_max_size)]:
                        if message.reference is not None:
                            await message.reply(x)
                        else:
                            await message.channel.send(x)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            # await message.channel.send(f"Unexpected {err=}, {type(err)=}")

            websocket_log(f"``Unexpected {err=}, {type(err)=}``")
        else:
            return

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.model_set = "arzaan789/qwen2-0.5b-uncensored:Q8_0"
client.webhook = os.environ['DISCORD_API_WEBHOOK']

# @client.tree.command(name='commandname', description="My first application Command")
# async def joinvc(interaction: discord.Interaction):
#     try:
#         await interaction.user.voice.channel.connect()
#         await interaction.response.send_message("Connected to Voice Channel!")
#     except Exception as err:
#         print(f"Unexpected {err=}, {type(err)=}")
#         # await message.channel.send(f"Unexpected {err=}, {type(err)=}")

#         websocket_log(f"``Unexpected {err=}, {type(err)=}``")

async def embed_msg(interaction: discord.Interaction, description, colour: int | Colour | None = None):
    await interaction.response.send_message(embed=Embed(title="Brok Response", description=description, colour=colour))

@client.tree.command(name='eval', description="*Owner only command*", guild=MAIN_GUILD)
@commands.is_owner()
async def command_eval(interaction: discord.Interaction, code: str):
    try:
        if interaction.user.id == BOT_OWNER:
            await embed_msg(interaction, eval(code))
        else:
            await embed_msg(interaction, "Access denied: Not the Owner.", 0xFF0000)
    except Exception as err:
        msg = f"Unexpected {err=}, {type(err)=}"
        print(msg)
        await embed_msg(interaction, msg, 0xFF0000)

class BrokCommands(Enum):
    list = 1
    load = 2
    unload = 3
    sync = 4

@client.tree.command(name='command', description="*Owner only command*", guild=MAIN_GUILD)
async def command(interaction: discord.Interaction, action: BrokCommands, value: str | None):
    try:
        if interaction.user.id == BOT_OWNER:
            models_list = await openaiapi.models.list()
            match action:
                case BrokCommands.list:
                    msg = ""
                    for x in models_list.data:
                        msg += f"``{x.id}``\n"
                    await embed_msg(interaction, msg)
                case BrokCommands.load:
                    if value != None:
                        for x in models_list.data:
                            if x.id == value:
                                await embed_msg(interaction, f"Changing model: ``{x.id}``")
                                client.model_set = x.id
                    else:
                        await embed_msg(interaction, "``name`` can't be empty for this command.", 0xFF0000)
                case BrokCommands.unload:
                    if value != None:
                        if value == "all":
                            for x in models_list.data:
                                unload(x)
                            await embed_msg(interaction, "done.")
                        else:
                            for x in models_list.data:
                                if x.id == value:
                                    unload(x)
                                    await embed_msg(interaction, "done.")
                                    break
                            await embed_msg(interaction, f"``{value}`` not found.", 0xFF0000)
                    else:
                        await embed_msg(interaction, "``value`` can't be empty for this command.", 0xFF0000)
                case BrokCommands.sync:
                    await client.tree.sync(guild=discord.Object(id=int(value)) if value != None else None)
                    await embed_msg(interaction, "done.")
        else:
            await embed_msg(interaction, "Access denied: Not the Owner.", 0xFF0000)
    except Exception as err:
        msg = f"Unexpected {err=}, {type(err)=}"
        print(msg)
        await embed_msg(interaction, msg, 0xFF0000)

@client.tree.command(name='ask', description="Ask brok a question.")
@app_commands.allowed_installs(guilds=True, users=True)
async def command_ask(interaction: discord.Interaction, message: str):
    try:
        listofmessages = [
            # {"role": "system", "content": client.create_system_prompt(interaction.message)}, 
            {"role": "user", "content": message}
        ]
        response = await openaiapi.chat.completions.create(
            model=client.model_set,
            messages=listofmessages,
        )

        response = response.choices[0].message.content

        print(response)

        regex_response = re.sub(r'@(?=(?!\s)\w)|(?=<)@(?=(|&)\d*>)', '\\@', response, flags=re.DOTALL)
        await interaction.response.send_message(content=regex_response)
    except Exception as err:
        msg = f"Unexpected {err=}, {type(err)=}"
        print(msg)
        await embed_msg(interaction, msg, 0xFF0000)

client.run(os.environ['DISCORD_API_KEY'])
