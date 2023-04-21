import discord
from discord.ext import commands
import config
from english_words import get_english_words_set
import random
import sqlite3

web2lowerset = get_english_words_set(['web2'], lower=True)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=config.prefix, intents=intents) 

con_ids = sqlite3.connect("ids.db")
cur_ids = con_ids.cursor()

con_words = sqlite3.connect("words.db")
cur_words = con_words.cursor()

englishwords = cur_words.execute(f"""SELECT en FROM translates""").fetchall()
russianwords = cur_words.execute(f"""SELECT ru FROM translates""").fetchall()

@bot.command()
async def translate(ctx):
    bot.remove_command("reply")
    
    if ctx.author not in cur_ids.execute(f"""SELECT id FROM options""").fetchall():
        cur_ids.execute(f"""INSERT INTO options(id, language) VALUES('{ctx.author}', 'en')""")

    options = [i[0] for i in cur_ids.execute(f"""SELECT language FROM options WHERE id = '{ctx.author}'""").fetchall()]


    if "ru" in options:
        output = random.choice(russianwords)[0]
        answer = cur_words.execute(f'''SELECT en FROM translates WHERE ru = "{output}"''').fetchall()

    else:
        output = random.choice(englishwords)[0]
        answer = cur_words.execute(f'''SELECT ru FROM translates WHERE en = "{output}"''').fetchall()

    answer = [i[0] for i in answer]

    await ctx.reply(output)

    con_ids.commit()
    @bot.command()
    async def reply(ctx, message="", additional=""):
        if message != "":
            if additional != "":
                message = message.lower().replace("ё", "") + " " + additional
            else:
                message = message.lower().replace("ё", "")

            if message in answer:
                if cur_ids.execute(f"""SELECT id FROM results WHERE id = '{ctx.author}'""").fetchall() == []:
                    cur_ids.execute(f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
                    cur_ids.execute(f"""UPDATE results SET points = 1 WHERE id = '{ctx.author}'""")
                    points = 1
                else:
                    points = int(cur_ids.execute(f"""SELECT points FROM results WHERE id = '{ctx.author}'""").fetchall()[0][0]) + 1
                    cur_ids.execute(f"""UPDATE results SET points = {points} WHERE id = '{ctx.author}'""")

                con_ids.commit()
                await ctx.reply(f"Верно! Ваш счёт: {points}.")

            else:
                await ctx.reply(f"Неверно! Возможные варианты перевода - {', '.join(answer)}")
                
        else:
            await ctx.reply(f"Ошибка! Попробуйте ввести ответ ещё раз.")


@bot.command()
async def settings(ctx, *options):
    if ctx.author not in cur_ids.execute(f"""SELECT id FROM options""").fetchall(): 
        cur_ids.execute(f"""INSERT INTO options(id, language) VALUES('{ctx.author}', 'en')""")
        con_ids.commit()
    
    p_options = cur_ids.execute(f"""SELECT language FROM options WHERE id = '{ctx.author}'""").fetchall()
    if len(options) == 0 or options == []:
        await ctx.reply(f"Ваши настройки:\n-language: {p_options[0][0]}.")

    else:
        if "-language" in options:
            try:
                if options[options.index("-language") + 1] == "ru":
                    cur_ids.execute(f"""UPDATE options SET language = 'ru' WHERE id = '{ctx.author}'""")
                elif options[options.index("-language") + 1] == "en":
                    cur_ids.execute(f"""UPDATE options SET language = 'en' WHERE id = '{ctx.author}'""")
                
                con_ids.commit()
                await ctx.reply(f"Настройки успешно изменены!")
            
            except IndexError:
                await ctx.reply(f"Ошибка! Попробуйте ввести настройки ещё раз.")




if __name__ == "__main__":
    bot.run(config.token)