import discord
from discord.ext import commands
import config
from english_words import get_english_words_set
import random
import sqlite3
import asyncio

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
async def start(ctx):
    bot.remove_command("reply") 
    if str(ctx.author) not in [i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()]:
        cur_ids.execute(f"""INSERT INTO options(id, language, mode, timer) VALUES('{ctx.author}', 'en', 'single', none)""")

    options = [i for i in cur_ids.execute(f"""SELECT language, mode, timer FROM options WHERE id = '{ctx.author}'""").fetchall()[-1]]

    if "ru" in options:
        output = random.choice(russianwords)[0]
        answer = [j[0] for j in cur_words.execute(f'''SELECT en FROM translates WHERE ru = "{output}"''').fetchall()]

    else:
        output = random.choice(englishwords)[0]
        answer = [j[0] for j in cur_words.execute(f'''SELECT ru FROM translates WHERE en = "{output}"''').fetchall()]

    await ctx.send(output)

    con_ids.commit()
    
    def check(message):
        return message.author.id == ctx.author.id
    
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
        
        
        if "auto" in options:
            asyncio.run_coroutine_threadsafe(start(ctx), bot.loop)
        else:
            pass
    

    try:
        m = await bot.wait_for("message", check=check, timeout = options[2])
    except asyncio.TimeoutError:
        bot.remove_command("reply") 
        await ctx.send(f"{ctx.author.mention} Время ответа вышло!")
    

@bot.command()
async def cancel(ctx):
    bot.remove_command("reply")
    await ctx.reply(f"Ввод отменён!")
    

@bot.command()
async def settings(ctx, *options):
    if str(ctx.author) not in [i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()]: 
        cur_ids.execute(f"""INSERT INTO options(id, language, mode, timer) VALUES('{ctx.author}', 'en', 'single', 'none')""")
        con_ids.commit()
    
    p_options = [i for i in cur_ids.execute(f"""SELECT language, mode, timer FROM options WHERE id = '{ctx.author}'""").fetchall()[-1]]
    if len(options) == 0 or options == []:
        await ctx.reply(f"Ваши настройки:\n-language: {p_options[0]}.\n-mode: {p_options[1]}.\n-timer:{p_options[2]}")

    else:
        try:
            if "-language" in options:
                if options[options.index("-language") + 1] == "ru":
                    cur_ids.execute(f"""UPDATE options SET language = 'ru' WHERE id = '{ctx.author}'""")
                elif options[options.index("-language") + 1] == "en":
                    cur_ids.execute(f"""UPDATE options SET language = 'en' WHERE id = '{ctx.author}'""")
                else:
                    raise IndexError
                
                con_ids.commit()
            
            if "-mode" in options:
                if options[options.index("-mode") + 1] == "auto":
                    cur_ids.execute(f"""UPDATE options SET mode = 'auto' WHERE id = '{ctx.author}'""")
                elif options[options.index("-mode") + 1] == "single":
                    cur_ids.execute(f"""UPDATE options SET mode = 'single' WHERE id = '{ctx.author}'""")
                else:
                    raise IndexError
                
                con_ids.commit()

            if "-timer" in options:
                if options[options.index("-timer") + 1].isdigit():
                    if int(options[options.index("-timer") + 1]) in range(1, 61):
                        cur_ids.execute(f"""UPDATE options SET timer = '{options[options.index("-timer") + 1]}' WHERE id = '{ctx.author}'""")
                    else:
                        await ctx.send(f'Параметр "-timer" должен быть в промежутке от 1 до 60 секунд.')
                        raise IndexError
                else:
                    raise IndexError
                
                con_ids.commit()

            await ctx.reply(f"Настройки успешно изменены!")

        except IndexError:
            await ctx.reply(f"Ошибка! Попробуйте изменить настройки ещё раз.")
        
        


if __name__ == "__main__":
    bot.run(config.token)