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
web2lowerset = ["bad", "good"]

con = sqlite3.connect("scores.db")
cur = con.cursor()

@bot.command()
async def translate(ctx):
    output = random.choice(list(web2lowerset))
    
    
    url = "https://microsoft-translator-text.p.rapidapi.com/translate"

    querystring = {"to[0]":"ru","api-version":"3.0","profanityAction":"NoAction","textType":"plain"}

    payload = [{"Text": output}]
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "5ae9d6a133mshe6372b0ccf5e37bp10183ajsn73865becc77e",
        "X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com"
    }

    response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

    await ctx.reply(output)

    @bot.command()
    async def reply(ctx, message):
        answer = response.json()[0]["translations"][0]["text"]
        print(response.text)
        if message == answer:
            author_id = cur.execute(f"""SELECT id FROM results WHERE id = '{ctx.author}'""").fetchall()
            print(author_id)
            if author_id == []:
                cur.execute(f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
                cur.execute(f"""UPDATE results SET points = 1 WHERE id = '{ctx.author}'""")
                points = 1
            else:
                print(cur.execute(f"""SELECT points FROM results WHERE id = '{ctx.author}'""").fetchall()[0])
                points = int(cur.execute(f"""SELECT points FROM results WHERE id = '{ctx.author}'""").fetchall()[0][0]) + 1
                cur.execute(f"""UPDATE results SET points = {points} WHERE id = '{ctx.author}'""")

            con.commit()
            await ctx.reply(f"Верно! Ваш счёт: {points}")

        else:
            await ctx.reply(f"Неверно! Правильный ответ - {answer}")
        bot.remove_command("reply")

if __name__ == "__main__":
    bot.run(config.token)