from datetime import datetime
import random
from llama_cpp import Llama
import discord
import re
import os

llm = Llama.from_pretrained(
    repo_id="Qwen/Qwen2.5-0.5B-Instruct-GGUF",
    filename="*q8_0.gguf",
    n_gpu_layers=37, # Uncomment to use GPU acceleration
    # seed=1337, # Uncomment to set a specific seed
    n_ctx=4096, # Uncomment to increase the context window
)

message_max_size = 2000

class MyClient(discord.Client):
    async def generate_message(self, message, systemprompt):            
        print(systemprompt)

        reply_message = None if message.reference is None or client.get_channel(message.reference.channel_id) is None \
        else (await client.get_channel(message.reference.channel_id).fetch_message(message.reference.message_id))

        print(reply_message)

        listofmessages = [{"role": "system", "content": systemprompt}]
        if reply_message is not None and reply_message.author is not client.user:
            listofmessages.append({"role": "assistant", "content": reply_message.content})
        listofmessages.append({"role": "user", "content": message.content})

        # print(listofmessages)
        
        response = llm.create_chat_completion(
            messages=listofmessages,
            # max_tokens=llm.context_params.n_ctx / 4,
            # max_tokens=128,
        )['choices'][0]['message']['content']

        print(response)

        # regex_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)

        # if regex_response is response:
        #     raise RuntimeError("The model didn't finish thinking! (Is the context window too small?)")

        # return regex_response
        return response

    async def on_ready(self):
        self.appinfo = await self.application_info()
        print(f'Logged on as {self.user}!')
        # if not hasattr(MyClient, 'appinfo'):

    # def create_system_prompt(self, message):
    #     return """You are a helpful assistant.
    #     the time right now is """ + datetime.now().strftime('%A, %B %d, %Y %I:%M:%S %p') + """.
    #     in this online chatroom you are mentioned as \"<@""" + str(self.appinfo.id) + """>\".
    #     the next message is from """ + str(message.author) + """ (mentioned as: <@""" + str(message.author.id) + """>).
    #     play into the act that you are president obama that uses his ***Emergency Presidential*** stash of things,
        # owns a mountain in colorado""" + (", use \"" + str(random.choice(message.guild.emojis)) + "\", \"" + str(random.choice(message.guild.emojis)) + "\", and \"" + str(random.choice(message.guild.emojis)) + "\" alot in your writing." if message.guild is not None else ".")

    def create_system_prompt(self, message):
        return """You are a helpful assistant.
        the time right now is """ + datetime.now().strftime('%A, %B %d, %Y %I:%M:%S %p') + """.
        in this online chatroom you are mentioned as \"<@""" + str(self.appinfo.id) + """> (you as in the helpful assistant that you are.)\".
        the next message is from """ + str(message.author) + """ (mentioned as: <@""" + str(message.author.id) + """>) (as in the person asking you a question.).
        Please keep your response short!"""

    async def on_message(self, message):
        try:
            if message.author.bot:
                return
            
            if message.author.id !=  discord.AppInfo.id:
                print(f'Message from {message.author}: {message.content}')

            if message.author == self.user:
                return
            
            if message.channel.type == discord.ChannelType.private or message.channel.name == "brok" or self.appinfo.id in map(lambda s: s.id,message.mentions):
                async with message.channel.typing():
                    response = await self.generate_message(message, self.create_system_prompt(message)) 

                    for x in [response[y-message_max_size:y] for y in range(message_max_size, len(response)+message_max_size,message_max_size)]:
                        await message.channel.send(x)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            await message.channel.send(f"Unexpected {err=}, {type(err)=}")
        else:
            return

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(os.environ['API_KEY'])
