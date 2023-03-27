import discord # Подключаем библиотеку
from discord.ext import commands

intents = discord.Intents.default() # Подключаем "Разрешения"
intents.message_content = True
# Задаём префикс и интенты
bot = commands.Bot(command_prefix='>', intents=intents) 

# С помощью декоратора создаём первую команду
@bot.command()
async def ping(ctx):
    await ctx.send('pong')


bot.run('MTA4OTg4MjA1NjIwMjM5OTc3NQ.GUksMk.cJQdg3F60L_oPVyxHQ8hb5KMEnF6uZ84n82GGE')