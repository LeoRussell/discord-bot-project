import discord
from discord.ext import commands
import requests
import config

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=config.prefix, intents=intents) 



@bot.command()
async def map(ctx, latitude="1", longitude="1", zoom="15", pic="map"):
    if not (latitude.replace("-", "")).isdigit():
        await ctx.reply("latitude par must be integer!")
    elif not (longitude.replace("-", "")).isdigit():
        await ctx.reply("longitude par must be integer!")
    elif not (zoom.replace("-", "")).isdigit():
        await ctx.reply("zoom par must be integer!")
    elif not (pic).isalpha():
        await ctx.reply("pic par must be string!")
    else:
        if not(int(latitude) in range(-86, 87)):
            await ctx.reply("latitude par must be in range(-86, 87)!")
        elif not(int(longitude) in range(-180, 181)):
            await ctx.reply("longitude par must be in range(-180, 181)!")
        elif not(int(zoom) in range(1, 17)):
            await ctx.reply("zoom par must be in range(1, 17)!")
        elif pic != "sat" or pic != "map":
            await ctx.reply('pic par must be "map" or "sat"')
        else:
            map_request = f"https://static-maps.yandex.ru/1.x/?ll={longitude},{latitude}&z={zoom}&l={pic}"
            response = requests.get(map_request)
            map_file = "map.jpg"
            with open(map_file, "wb") as file:
                file.write(response.content)
                
            await ctx.reply(file=discord.File('map.jpg'))


if __name__ == "__main__":
    bot.run(config.token)