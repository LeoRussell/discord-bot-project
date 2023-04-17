import discord
from discord.ext import commands
import requests
import config
from english_words import get_english_words_set
import random

web2lowerset = get_english_words_set(['web2'], lower=True)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=config.prefix, intents=intents) 
web2lowerset = ["bad", "good"]


@bot.command()
async def translate(ctx):
    output = random.choice(list(web2lowerset))
    await ctx.reply(output)
    
    url = "https://microsoft-translator-text.p.rapidapi.com/BreakSentence"

    querystring = {"api-version":"3.0"}

    payload = [{"Text": output}]
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "5ae9d6a133mshe6372b0ccf5e37bp10183ajsn73865becc77e",
        "X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com"
    }

    response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

    print(response.text)
    @bot.command()
    async def reply(ctx, message):
        if message == response.text:
            await ctx.reply("Верно!")
        else:
            await ctx.reply(f"Неверно! Правильный ответ - {response.text}")
            print(response.text)


if __name__ == "__main__":
    bot.run(config.token)