import discord
from discord.ext import commands
import requests
import config
from english_words import get_english_words_set
import random
import sqlite3

web2lowerset = get_english_words_set(['web2'], lower=True)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=config.prefix, intents=intents) 

con_score = sqlite3.connect("scores.db")
cur_score = con_score.cursor()

con_words = sqlite3.connect("words.db")
cur_words = con_words.cursor()

englishwords = cur_words.execute(f"""SELECT en FROM translates""").fetchall()
russianwords = cur_words.execute(f"""SELECT ru FROM translates""").fetchall()

@bot.command()
async def translate(ctx):
    output = random.choice(englishwords)[0]

    answer = cur_words.execute(f'''SELECT ru FROM translates WHERE en = "{output}"''').fetchall()
    answer = [i[0] for i in answer]

    await ctx.reply(output)

    @bot.command()
    async def reply(ctx, message):
        message = message.lower().replace("ё", "")
        if message in answer:
            author_id = cur_score.execute(f"""SELECT id FROM results WHERE id = '{ctx.author}'""").fetchall()
            if author_id == []:
                cur_score.execute(f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
                cur_score.execute(f"""UPDATE results SET points = 1 WHERE id = '{ctx.author}'""")
                points = 1
            else:
                points = int(cur_score.execute(f"""SELECT points FROM results WHERE id = '{ctx.author}'""").fetchall()[0][0]) + 1
                cur_score.execute(f"""UPDATE results SET points = {points} WHERE id = '{ctx.author}'""")

            con_score.commit()
            await ctx.reply(f"Верно! Ваш счёт: {points}.")
            await ctx.reply(f"Возможные варианты перевода: {', '.join(answer)}.")

        else:
            await ctx.reply(f"Неверно! Правильный ответ - {', '.join(answer)}")
            
        bot.remove_command("reply")

if __name__ == "__main__":
    bot.run(config.token)