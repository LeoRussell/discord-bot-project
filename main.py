import discord
from discord.ext import commands
from english_words import get_english_words_set
import config
import random
import sqlite3
import asyncio
import requests



intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=config.prefix, intents=intents) 

con_ids = sqlite3.connect("ids.db")
cur_ids = con_ids.cursor()

con_words = sqlite3.connect("language.db")
cur_words = con_words.cursor()

web2lowerset = get_english_words_set(['web2'], lower=True)

englishwords = cur_words.execute(f"""SELECT en FROM translates""").fetchall()
russianwords = cur_words.execute(f"""SELECT ru FROM translates""").fetchall()


@bot.command()
async def traducere(ctx, message=None):
    bot.remove_command("reply") 
    if str(ctx.author) not in [i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()]:
        cur_ids.execute(f"""INSERT INTO options(id, language, mode, timer) VALUES('{ctx.author}', 'en', 'single', '5')""")
        con_ids.commit()
    
    options = [i for i in cur_ids.execute(f"""SELECT language, mode, timer FROM options WHERE id = '{ctx.author}'""").fetchall()[-1]]

    if message == "auto":
        options[1] = "auto"

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
                else:
                    points = int(cur_ids.execute(f"""SELECT points FROM results WHERE id = '{ctx.author}'""").fetchall()[0][0]) + 1
                    cur_ids.execute(f"""UPDATE results SET points = {points} WHERE id = '{ctx.author}'""")

                con_ids.commit()
                await ctx.reply(f"Верно!")

            else:
                await ctx.reply(f"Неверно! Возможные варианты перевода - {', '.join(answer)}")
                
        else:
            await ctx.reply(f"Ошибка! Попробуйте ввести ответ ещё раз.")
        
        
        if "auto" in options:
            asyncio.run_coroutine_threadsafe(traducere(ctx), bot.loop)
        else:
            pass
    

    try:
        m = await bot.wait_for("message", check=check, timeout = int(options[2]))
    except asyncio.TimeoutError:
        bot.remove_command("reply") 
        await ctx.send(f"{ctx.author.mention} Время ответа вышло!")
    

@bot.command()
async def cancel(ctx):
    bot.remove_command("reply")
    await ctx.reply(f"Ввод отменён!")
    

@bot.command()
async def language(ctx, par=None):
    if str(ctx.author) not in [i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()]: 
        cur_ids.execute(f"""INSERT INTO options(id, language, timer) VALUES('{ctx.author}', 'en', '15')""")
        con_ids.commit()
    
    lang = [i for i in cur_ids.execute(f"""SELECT language FROM options WHERE id = '{ctx.author}'""").fetchall()[-1]][0]
    
    if par == None:
        await ctx.reply(f"Выбранный язык для игры переводчика: {lang.upper()}.")
    
    elif par == "ru" or par == "en":
        cur_ids.execute(f"""UPDATE options SET language = '{par}' WHERE id = '{ctx.author}'""")
        con_ids.commit()
        await ctx.reply("Значения успешно изменены!")

    else:
        await ctx.reply(f"Ошибка! Проверьте правильность введенных вами данных!")

    
@bot.command()
async def timer(ctx, par=None, time=None):
    if str(ctx.author) not in [i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()]: 
        cur_ids.execute(f"""INSERT INTO options(id, language, timer) VALUES('{ctx.author}', 'en', '15')""")
        con_ids.commit()
    
    timesettings = [i for i in cur_ids.execute(f"""SELECT timer FROM options WHERE id = '{ctx.author}'""").fetchall()[-1]][0]
    
    if par == None:
        await ctx.reply(f"Выбранное время ожидание ответа: {timesettings}")
    
    elif par.isdigit():
        secondint = int(par)
        if secondint > 300:
            await ctx.send("Пожалуйста, введите кол-во секунд до 300.")
            raise BaseException
        if secondint <= 0:
            await ctx.send("Пожалуйста, введите число больше 0.")
            raise BaseException
        message = await ctx.send(f"Таймер: {int(par)}")
        while True:
            secondint -= 1
            if secondint == 0:
                await message.edit(content="Окончен!")
                break
            await message.edit(content=f"Таймер: {secondint}")
            await asyncio.sleep(1)
        await ctx.send(f"{ctx.author.mention} Отсчёт завершен!")
    
    elif par == "set":
        try:
            if int(time) in range(1, 300):
                cur_ids.execute(f"""UPDATE options SET timer = '{time}' WHERE id = '{ctx.author}'""")
                con_ids.commit()
                await ctx.reply("Значения успешно изменены!")

            else:
                await ctx.send("Параметр time должен быть числом от 1 до 300!")

        except TypeError:
            await ctx.send("Параметр time должен быть числом!")
        except ValueError:
            await ctx.send("Параметр time должен быть числом!")

    else:
        await ctx.send(f"Ошибка! Проверьте правильность введенных вами данных!")


@bot.command()
async def translate(ctx, *message):
    message = (" ".join(message)).replace('"', '')

    url = "https://microsoft-translator-text.p.rapidapi.com/translate"

    querystring = {"to[0]":"ru","api-version":"3.0","profanityAction":"NoAction","textType":"plain"}

    payload = [{ "Text": message}]
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "5ae9d6a133mshe6372b0ccf5e37bp10183ajsn73865becc77e",
        "X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com"
    }

    response = requests.post(url, json=payload, headers=headers, params=querystring)

    await ctx.reply(f"{response.json()[0]['translations'][0]['text']}")


@bot.command()
async def top(ctx, num=10):
    if cur_ids.execute(f"""SELECT id FROM results WHERE id = '{ctx.author}'""").fetchall() == []:
        cur_ids.execute(f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
        cur_ids.execute(f"""UPDATE results SET points = 1 WHERE id = '{ctx.author}'""")
        con_ids.commit()

    results = cur_ids.execute(f"""SELECT id, points FROM results""").fetchall()
    dict_results = dict()
    for i in results:
        dict_results[i[0]] = int(i[1])
    
    sorted_dict = {}
    sorted_keys = sorted(dict_results, key=dict_results.get, reverse=True)

    for j in sorted_keys:
        sorted_dict[j] = dict_results[j]

    output = f"Топ сервера по очкам на данный момент:\n"
    n = 0
    for i in sorted_dict.keys():
        if n == num:
            break
        output += f"{i} – {sorted_dict[i]}\n"
        n += 1
    
    await ctx.send(output)


@bot.command()
async def words(ctx):
    bot.remove_command("reply")
    if str(ctx.author) not in [i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()]:
        cur_ids.execute(f"""INSERT INTO options(id, language, mode, timer) VALUES('{ctx.author}', 'en', 'single', '5')""")
        con_ids.commit()

    options = [i for i in cur_ids.execute(f"""SELECT language, mode, timer FROM options WHERE id = '{ctx.author}'""").fetchall()[-1]]


    word = random.choice(list(web2lowerset))
    await ctx.reply(word)
    
    def check(message):
        return message.author.id == ctx.author.id
    
    @bot.command()
    async def reply(ctx, answer):
        if answer[0] == word[-1]:
            if answer in list(web2lowerset):
                if cur_ids.execute(f"""SELECT id FROM results WHERE id = '{ctx.author}'""").fetchall() == []:
                    cur_ids.execute(f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
                    cur_ids.execute(f"""UPDATE results SET points = 1 WHERE id = '{ctx.author}'""")
                else:
                    points = int(cur_ids.execute(f"""SELECT points FROM results WHERE id = '{ctx.author}'""").fetchall()[0][0]) + 1
                    cur_ids.execute(f"""UPDATE results SET points = {points} WHERE id = '{ctx.author}'""")
                
                con_ids.commit()

                asyncio.run_coroutine_threadsafe(words(ctx), bot.loop)
            else:
                await ctx.send("Хм, этого слова нет в моей базе данных. Попробуй ещё раз!")
        else:
            await ctx.reply(f'Слово должно начинаться с полследней буквы "{word.upper()}"')

    try:
        m = await bot.wait_for("message", check=check, timeout = int(options[2]))
    except asyncio.TimeoutError:
        bot.remove_command("reply") 
        await ctx.send(f"{ctx.author.mention} Время ответа вышло!")


@bot.command()
async def statistic(ctx):
    if str(ctx.author) not in [i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()]:
        cur_ids.execute(f"""INSERT INTO options(id, language, mode, timer) VALUES('{ctx.author}', 'en', 'single', '5')""")
    
    if cur_ids.execute(f"""SELECT id FROM results WHERE id = '{ctx.author}'""").fetchall() == []:
                    cur_ids.execute(f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
                    cur_ids.execute(f"""UPDATE results SET points = '0' WHERE id = '{ctx.author}'""")
    
    con_ids.commit()

    stats = cur_ids.execute(f"""SELECT points FROM results WHERE id = '{ctx.author}'""").fetchall()

    results = cur_ids.execute(f"""SELECT id, points FROM results""").fetchall()
    dict_results = dict()
    for i in results:
        dict_results[i[0]] = int(i[1])
    
    sorted_keys = sorted(dict_results, key=dict_results.get, reverse=True)
    place_in_top = sorted_keys.index(str(ctx.author)) + 1
    output = f"{ctx.author.mention}\nКоличество очков: {stats[0][0]}.\nМесто в топе: {place_in_top}"

    await ctx.reply(output)


@bot.command()
async def countries(ctx):
    bot.remove_command("reply")
    if str(ctx.author) not in [i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()]:
        cur_ids.execute(f"""INSERT INTO options(id, language, mode, timer) VALUES('{ctx.author}', 'en', 'single', '5')""")
        con_ids.commit()

    options = [i for i in cur_ids.execute(f"""SELECT language, mode, timer FROM options WHERE id = '{ctx.author}'""").fetchall()[-1]]

    countries_list = cur_words.execute(f"""SELECT country, city FROM cities""").fetchall()

    right_cc = random.choice(countries_list)
    cities = [random.choice(countries_list)[1], random.choice(countries_list)[1], right_cc[1]]
    random.shuffle(cities)

    await ctx.reply(f'Выберите правильный вариант ответа.\
                    \n Столицей страны {right_cc[0]} является...: \
                    \n1. {cities[0]}.\n2. {cities[1]}.\n3. {cities[2]}.')
    
    def check(message):
        return message.author.id == ctx.author.id
    

    @bot.command()
    async def reply(ctx, answer):
        if answer.isdigit():
            try:
                if cities[int(answer) - 1] == right_cc[1]:
                    if cur_ids.execute(f"""SELECT id FROM results WHERE id = '{ctx.author}'""").fetchall() == []:
                        cur_ids.execute(f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
                        cur_ids.execute(f"""UPDATE results SET points = 1 WHERE id = '{ctx.author}'""")
                    else:
                        points = int(cur_ids.execute(f"""SELECT points FROM results WHERE id = '{ctx.author}'""").fetchall()[0][0]) + 1
                        cur_ids.execute(f"""UPDATE results SET points = {points} WHERE id = '{ctx.author}'""")
                    
                    con_ids.commit()

                    await ctx.send("Верно!")
                    asyncio.run_coroutine_threadsafe(countries(ctx), bot.loop)
                else:
                    await ctx.send(f"Ответ неверный! Правильный ответ - {right_cc[1]}.")
            except IndexError:
                await ctx.reply(f'Ответ неверный! Правильный ответ - {right_cc[1]}')   
        else:
            await ctx.reply(f'Ответ должен быть цифрой! Попробуйте ещё раз.')

    try:
        m = await bot.wait_for("message", check=check, timeout = int(options[2]))
    except asyncio.TimeoutError:
        bot.remove_command("reply") 
        await ctx.send(f"{ctx.author.mention} Время ответа вышло!")


if __name__ == "__main__":
    bot.run(config.token)