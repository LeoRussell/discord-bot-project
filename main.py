from webserver import keep_alive
import discord
from discord.ext import commands
from english_words import get_english_words_set
import config
import random
import sqlite3
import asyncio
import requests

keep_alive()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=config.prefix, intents=intents)
bot.remove_command("help")

con_ids = sqlite3.connect("ids.db")
cur_ids = con_ids.cursor()

con_words = sqlite3.connect("language.db")
cur_words = con_words.cursor()

web2lowerset = get_english_words_set(['web2'], lower=True)

englishwords = cur_words.execute(f"""SELECT en FROM translates""").fetchall()
russianwords = cur_words.execute(f"""SELECT ru FROM translates""").fetchall()


@bot.command(name="traducere")
async def traducere(ctx, par=None, spar=None):
  if str(ctx.author) not in [
      i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()
  ]:
    cur_ids.execute(
      f"""INSERT INTO options(id, language, timer, queue) VALUES('{ctx.author}', 'en', '15', 'None')"""
    )
    con_ids.commit()

  options = [
    i for i in cur_ids.execute(
      f"""SELECT language, timer FROM options WHERE id = '{ctx.author}'""").
    fetchall()[-1]
  ]
  cur_lang = options[0]

  queue = [
    i for i in cur_ids.execute(
      f"""SELECT id FROM options WHERE queue = 'taken'""").fetchall()
  ]
  if queue == [] or queue == [(str(ctx.author), )]:
    bot.remove_command("reply")
    cur_ids.execute(
      f"""UPDATE options SET queue = 'taken' WHERE id = '{ctx.author}'""")

    if (par in ["loop", "ru", "en", None]) and (spar
                                                in ["loop", "ru", "en", None]):
      if "ru" == par or "ru" == spar:
        output = random.choice(russianwords)[0]
        answer = [
          j[0] for j in cur_words.execute(
            f'''SELECT en FROM translates WHERE ru = "{output}"''').fetchall()
        ]

      else:
        output = random.choice(englishwords)[0]
        answer = [
          j[0] for j in cur_words.execute(
            f'''SELECT ru FROM translates WHERE en = "{output}"''').fetchall()
        ]

      con_ids.commit()

      await ctx.send(f"> {output.capitalize()}")

      def check(message):
        return message.author.id == ctx.author.id

      @bot.command()
      async def reply(ctx, message="", additional=""):
        queue = [
          i for i in cur_ids.execute(
            f"""SELECT id FROM options WHERE queue = 'taken'""").fetchall()
        ]
        if queue == [(str(ctx.author), )]:
          if message != "":
            if additional != "":
              message = message.lower().replace("ё", "") + " " + additional
            else:
              message = message.lower().replace("ё", "")

            if message in answer:
              if cur_ids.execute(
                  f"""SELECT id FROM results WHERE id = '{ctx.author}'"""
              ).fetchall() == []:
                cur_ids.execute(
                  f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
                cur_ids.execute(
                  f"""UPDATE results SET points = '1', combo = '1', highest_combo = '1' WHERE id = '{ctx.author}'"""
                )
              else:
                combo = int(
                  cur_ids.execute(
                    f"""SELECT combo FROM results WHERE id = '{ctx.author}'"""
                  ).fetchall()[0][0]) + 1
                highest_combo = int(
                  cur_ids.execute(
                    f"""SELECT highest_combo FROM results WHERE id = '{ctx.author}'"""
                  ).fetchall()[0][0])
                cur_ids.execute(
                  f"""UPDATE results SET combo = '{combo}' WHERE id = '{ctx.author}'"""
                )
                if int(combo) > int(highest_combo):
                  cur_ids.execute(
                    f"""UPDATE results SET highest_combo = '{combo}' WHERE id = '{ctx.author}'"""
                  )

                points = int(
                  cur_ids.execute(
                    f"""SELECT points FROM results WHERE id = '{ctx.author}'"""
                  ).fetchall()[0][0])
                if combo < 10:
                  cur_ids.execute(
                    f"""UPDATE results SET points = '{points + 1}' WHERE id = '{ctx.author}'"""
                  )
                elif combo < 25:
                  cur_ids.execute(
                    f"""UPDATE results SET points = '{points + 2}' WHERE id = '{ctx.author}'"""
                  )
                elif combo >= 50:
                  cur_ids.execute(
                    f"""UPDATE results SET points = '{points + 3}' WHERE id = '{ctx.author}'"""
                  )

              con_ids.commit()
              await ctx.reply(f"Верно!")

            else:
              if cur_ids.execute(
                  f"""SELECT id FROM results WHERE id = '{ctx.author}'"""
              ).fetchall() == []:
                cur_ids.execute(
                  f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
                cur_ids.execute(
                  f"""UPDATE results SET points = '0', combo = '0', highest_combo = '0' WHERE id = '{ctx.author}'"""
                )
              else:
                cur_ids.execute(
                  f"""UPDATE results SET combo = '0' WHERE id = '{ctx.author}'"""
                )

              if cur_lang == "ru":
                await ctx.reply(
                  f"Неверно! Возможные варианты перевода - `{', '.join(answer)}`."
                )
              else:
                await ctx.reply(
                  f"Wrong! Possible translations - `{', '.join(answer)}`.")

              cur_ids.execute(
                f"""UPDATE options SET queue = 'None' WHERE id = '{ctx.author}'"""
              )
              con_ids.commit()

              bot.remove_command("reply")

          else:
            if cur_lang == "ru":
              await ctx.reply(f"Ошибка! Попробуйте ввести ответ ещё раз.")
            else:
              await ctx.reply(f"Error! Please try again.")

          if par == "loop" or spar == "loop":
            asyncio.run_coroutine_threadsafe(traducere(ctx, par, spar),
                                             bot.loop)
          else:
            cur_ids.execute(
              f"""UPDATE options SET queue = 'None' WHERE id = '{ctx.author}'"""
            )
            con_ids.commit()

        else:
          if cur_lang == "ru":
            await ctx.reply(
              f"Ошибка! Пользователь **{queue[0][0]}** уже занимается!")
          else:
            await ctx.reply(
              f"Error! User **{queue[0][0]}** is already exercising")

      try:
        m = await bot.wait_for("message", check=check, timeout=int(options[1]))
      except asyncio.TimeoutError:
        bot.remove_command("reply")
        cur_ids.execute(
          f"""UPDATE options SET queue = 'None' WHERE id = '{ctx.author}'""")
        con_ids.commit()
        if cur_lang == "ru":
          await ctx.send(f"{ctx.author.mention} Время ответа вышло!")
        else:
          await ctx.send(f"{ctx.author.mention} Response time is up!")

    else:
      if cur_lang == "ru":
        await ctx.reply(f"Ошибка! Неверный параметр!")
      else:
        await ctx.reply(f"Error! Invalid parameter!")

  else:
    if cur_lang == "ru":
      await ctx.reply(f"Ошибка! Пользователь **{queue[0][0]}** уже занимается!"
                      )
    else:
      await ctx.reply(f"Error! User **{queue[0][0]}** is already exercising")
    cur_ids.execute(
      f"""UPDATE options SET queue = 'None' WHERE id = '{ctx.author}'""")
    con_ids.commit()


@bot.command(name="cancel")
async def cancel(ctx):
  if str(ctx.author) not in [
      i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()
  ]:
    cur_ids.execute(
      f"""INSERT INTO options(id, language, timer, queue) VALUES('{ctx.author}', 'en', '15', 'None')"""
    )
    con_ids.commit()

  cur_lang = [
    i for i in cur_ids.execute(
      f"""SELECT language, timer FROM options WHERE id = '{ctx.author}'""").
    fetchall()[-1]
  ][0]

  queue = [
    i for i in cur_ids.execute(
      f"""SELECT id FROM options WHERE queue = 'taken'""").fetchall()
  ]
  if queue == [(str(ctx.author), )]:
    bot.remove_command("reply")
    if cur_lang == "ru":
      await ctx.reply(f"Ввод **отменён!**")
    else:
      await ctx.reply(f"Input **canceled!**")
    cur_ids.execute(
      f"""UPDATE options SET queue = 'None' WHERE id = '{ctx.author}'""")
    con_ids.commit()

  elif queue == []:
    if cur_lang == "ru":
      await ctx.reply(f"Сейчас ничего не происходит!")
    else:
      await ctx.reply(f"Nothing is happening right now!")

  else:
    if cur_lang == "ru":
      await ctx.reply(f"Ошибка! Пользователь **{queue[0][0]}** уже занимается!"
                      )
    else:
      await ctx.reply(f"Error! User **{queue[0][0]}** is already exercising!")


@bot.command(name="language")
async def language(ctx, par=None):
  if str(ctx.author) not in [
      i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()
  ]:
    cur_ids.execute(
      f"""INSERT INTO options(id, language, timer, queue) VALUES('{ctx.author}', 'en', '15', 'None')"""
    )
    con_ids.commit()

  cur_lang = [
    i for i in cur_ids.execute(
      f"""SELECT language FROM options WHERE id = '{ctx.author}'""").fetchall(
      )[-1]
  ][0]

  if par == None:
    if cur_lang == "ru":
      await ctx.reply(f"Выбранный язык бота: {cur_lang.upper()}.")
    else:
      await ctx.reply(f"Selected bot language: {cur_lang.upper()}.")

  elif par == "ru" or par == "en":
    cur_ids.execute(
      f"""UPDATE options SET language = '{par}' WHERE id = '{ctx.author}'""")
    con_ids.commit()
    if par == "ru":
      await ctx.reply("Значения успешно изменены!")
    else:
      await ctx.reply("Values successfully changed!")

  else:
    if cur_lang == "ru":
      await ctx.reply(f"Ошибка! Проверьте правильность введенных вами данных!")
    else:
      await ctx.reply(
        f"Error! Checking the correctness of the data you entered!")


@bot.command(name="timer")
async def timer(ctx, par=None, time=None):
  if str(ctx.author) not in [
      i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()
  ]:
    cur_ids.execute(
      f"""INSERT INTO options(id, language, timer, queue) VALUES('{ctx.author}', 'en', '15', 'None')"""
    )
    con_ids.commit()

  cur_lang = [
    i for i in cur_ids.execute(
      f"""SELECT language FROM options WHERE id = '{ctx.author}'""").fetchall(
      )[-1]
  ][0]
  timesettings = [
    i for i in cur_ids.execute(
      f"""SELECT timer FROM options WHERE id = '{ctx.author}'""").fetchall()
    [-1]
  ][0]

  if par == None:
    if cur_lang == "ru":
      await ctx.reply(f"Выбранное время ожидание ответа: {timesettings}.")
    else:
      await ctx.reply(f"Selected response time: {timesettings}.")

  elif par.isdigit():
    secondint = int(par)
    if secondint > 300:
      if cur_lang == "ru":
        await ctx.send("Пожалуйста, введите количество секунд до 300.")
      else:
        await ctx.send("Please enter a number of seconds up to 300.")
      raise BaseException

    if secondint <= 0:
      if cur_lang == "ru":
        await ctx.send("Пожалуйста, введите число больше 0.")
      else:
        await ctx.send("Please enter a number bigger than 0.")
      raise BaseException

    if cur_lang == "ru":
      message = await ctx.send(f"Таймер: {int(par)}")
    else:
      message = await ctx.send(f"Timer: {int(par)}")

    while True:
      secondint -= 1
      if secondint == 0:
        if cur_lang == "ru":
          await message.edit(content="Окончен!")
        else:
          await message.edit(content="Ended!")
        break
      if cur_lang == "ru":
        await message.edit(content=f"Таймер: {secondint}")
      else:
        await message.edit(content=f"Timer: {secondint}")

      await asyncio.sleep(1)

    if cur_lang == "ru":
      await ctx.send(f"{ctx.author.mention} Отсчёт завершен!")
    else:
      await ctx.send(f"{ctx.author.mention} Countdown completed!")

  elif par == "set":
    try:
      if int(time) in range(1, 61):
        cur_ids.execute(
          f"""UPDATE options SET timer = '{time}' WHERE id = '{ctx.author}'""")
        con_ids.commit()

        if cur_lang == "ru":
          await ctx.reply("Значения успешно изменены!")
        else:
          await ctx.reply("Values successfully changed!")

      else:
        if cur_lang == "ru":
          await ctx.send("Параметр time должен быть числом от 1 до 60!")
        else:
          await ctx.send(
            "The time parameter must be a number between 1 and 60!")

    except TypeError:
      if cur_lang == "ru":
        await ctx.send("Параметр time должен быть числом!")
      else:
        await ctx.send("The time parameter must be a number!")

    except ValueError:
      if cur_lang == "ru":
        await ctx.send("Параметр time должен быть числом!")
      else:
        await ctx.send("The time parameter must be a number!")

  else:
    if cur_lang == "ru":
      await ctx.send(f"Ошибка! Проверьте правильность введенных вами данных!")
    else:
      await ctx.send(f"Error! Check the correctness of the data you entered!")


@bot.command(name="translate")
async def translate(ctx, message):
  url = "https://microsoft-translator-text.p.rapidapi.com/translate"

  querystring = {
    "to[0]": "ru",
    "api-version": "3.0",
    "profanityAction": "NoAction",
    "textType": "plain"
  }

  payload = [{"Text": message}]
  headers = {
    "content-type": "application/json",
    "X-RapidAPI-Key": "5ae9d6a133mshe6372b0ccf5e37bp10183ajsn73865becc77e",
    "X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com"
  }

  response = requests.post(url,
                           json=payload,
                           headers=headers,
                           params=querystring)

  await ctx.reply(f"{response.json()[0]['translations'][0]['text']}")


@bot.command(name="top")
async def top(ctx, par=10):
  if cur_ids.execute(f"""SELECT id FROM results WHERE id = '{ctx.author}'"""
                     ).fetchall() == []:
    cur_ids.execute(f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
    cur_ids.execute(
      f"""UPDATE results SET points = '1', combo = '0', highest_combo = '0' WHERE id = '{ctx.author}'"""
    )
    con_ids.commit()

  if str(ctx.author) not in [
      i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()
  ]:
    cur_ids.execute(
      f"""INSERT INTO options(id, language, timer, queue) VALUES('{ctx.author}', 'en', '15', 'None')"""
    )
    con_ids.commit()

  cur_lang = [
    i for i in cur_ids.execute(
      f"""SELECT language FROM options WHERE id = '{ctx.author}'""").fetchall(
      )[-1]
  ][0]

  results = cur_ids.execute(f"""SELECT id, points FROM results""").fetchall()
  dict_results = dict()
  for i in results:
    dict_results[i[0]] = int(i[1])

  sorted_dict = {}
  sorted_keys = sorted(dict_results, key=dict_results.get, reverse=True)

  for j in sorted_keys:
    sorted_dict[j] = dict_results[j]

  variantes = "Топ сервера" if cur_lang == 'ru' else "Server's top"

  output = f"**{variantes}**:\n"
  n = 0
  for i in sorted_dict.keys():
    if n == int(par):
      break
    output += f"*{n + 1}.* {i} – **{sorted_dict[i]}**.\n"
    n += 1

  await ctx.send(output)


@bot.command(name="words")
async def words(ctx):
  if str(ctx.author) not in [
      i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()
  ]:
    cur_ids.execute(
      f"""INSERT INTO options(id, language, timer, queue) VALUES('{ctx.author}', 'en', '15', 'None')"""
    )
    con_ids.commit()

  options = [
    i for i in cur_ids.execute(
      f"""SELECT language, timer FROM options WHERE id = '{ctx.author}'""").
    fetchall()[-1]
  ]
  cur_lang = options[0]

  queue = [
    i for i in cur_ids.execute(
      f"""SELECT id FROM options WHERE queue = 'taken'""").fetchall()
  ]
  if queue == [] or queue == [(str(ctx.author), )]:
    cur_ids.execute(
      f"""UPDATE options SET queue = 'taken' WHERE id = '{ctx.author}'""")
    bot.remove_command("reply")
    word = random.choice(list(web2lowerset))
    con_ids.commit()
    
    await ctx.reply(f"**{word.capitalize()}**")

    def check(message):
      return message.author.id == ctx.author.id

    @bot.command()
    async def reply(ctx, answer):
      queue = [
        i for i in cur_ids.execute(
          f"""SELECT id FROM options WHERE queue = 'taken'""").fetchall()
      ]
      if queue == [(str(ctx.author), )]:
        if answer[0] == word[-1]:
          if answer in list(web2lowerset):
            if cur_ids.execute(
                f"""SELECT id FROM results WHERE id = '{ctx.author}'"""
            ).fetchall() == []:
              cur_ids.execute(
                f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
              cur_ids.execute(
                f"""UPDATE results SET points = '1', combo = '1', highest_combo = '1' WHERE id = '{ctx.author}'"""
              )
            else:
              combo = int(
                cur_ids.execute(
                  f"""SELECT combo FROM results WHERE id = '{ctx.author}'""").
                fetchall()[0][0]) + 1
              highest_combo = int(
                cur_ids.execute(
                  f"""SELECT highest_combo FROM results WHERE id = '{ctx.author}'"""
                ).fetchall()[0][0])
              cur_ids.execute(
                f"""UPDATE results SET combo = '{combo}' WHERE id = '{ctx.author}'"""
              )
              if int(combo) > int(highest_combo):
                cur_ids.execute(
                  f"""UPDATE results SET highest_combo = '{combo}' WHERE id = '{ctx.author}'"""
                )

              points = int(
                cur_ids.execute(
                  f"""SELECT points FROM results WHERE id = '{ctx.author}'""").
                fetchall()[0][0])
              if combo < 10:
                cur_ids.execute(
                  f"""UPDATE results SET points = '{points + 1}' WHERE id = '{ctx.author}'"""
                )
              elif combo < 25:
                cur_ids.execute(
                  f"""UPDATE results SET points = '{points + 2}' WHERE id = '{ctx.author}'"""
                )
              elif combo >= 50:
                cur_ids.execute(
                  f"""UPDATE results SET points = '{points + 3}' WHERE id = '{ctx.author}'"""
                )

            con_ids.commit()

            asyncio.run_coroutine_threadsafe(words(ctx), bot.loop)
          else:
            if cur_ids.execute(
                f"""SELECT id FROM results WHERE id = '{ctx.author}'"""
            ).fetchall() == []:
              cur_ids.execute(
                f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
              cur_ids.execute(
                f"""UPDATE results SET points = '0', combo = '0', highest_combo = '0' WHERE id = '{ctx.author}'"""
              )
            else:
              cur_ids.execute(
                f"""UPDATE results SET combo = '0' WHERE id = '{ctx.author}'"""
              )

            con_ids.commit()

            if cur_lang == "ru":
              await ctx.send("Такого слова не существует!")
            else:
              await ctx.send("There is no such word!")
            asyncio.run_coroutine_threadsafe(words(ctx), bot.loop)

        else:
          if cur_lang == "ru":
            await ctx.reply(
              f'Слово должно начинаться с последней буквы **"{word.capitalize()}"**.'
            )
          else:
            await ctx.reply(
              f'The word must start with the last letter **"{word.capitalize()}"**.'
            )

      else:
        if cur_lang == "ru":
          await ctx.reply(
            f"Ошибка! Пользователь **{queue[0][0]}** уже занимается!")
        else:
          await ctx.reply(
            f"Error! User **{queue[0][0]}** is already exercising")

    try:
      m = await bot.wait_for("message", check=check, timeout=int(options[1]))
    except asyncio.TimeoutError:
      bot.remove_command("reply")
      cur_ids.execute(
        f"""UPDATE options SET queue = 'None' WHERE id = '{ctx.author}'""")
      con_ids.commit()
      if cur_lang == "ru":
        await ctx.send(f"{ctx.author.mention} Время ответа вышло!")
      else:
        await ctx.send(f"{ctx.author.mention} Response time out!")

  else:
    if cur_lang == "ru":
      await ctx.reply(f"Ошибка! Пользователь **{queue[0][0]}** уже занимается!"
                      )
    else:
      await ctx.reply(f"Error! User **{queue[0][0]}** is already exercising!")


@bot.command(name="statistic")
async def statistic(ctx):
  if str(ctx.author) not in [
      i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()
  ]:
    cur_ids.execute(
      f"""INSERT INTO options(id, language, timer, queue) VALUES('{ctx.author}', 'en', '15', 'None')"""
    )

  cur_lang = [
    i for i in cur_ids.execute(
      f"""SELECT language FROM options WHERE id = '{ctx.author}'""").fetchall(
      )[-1]
  ][0]

  if cur_ids.execute(f"""SELECT id FROM results WHERE id = '{ctx.author}'"""
                     ).fetchall() == []:
    cur_ids.execute(f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
    cur_ids.execute(
      f"""UPDATE results SET points = '0', combo = '0', highest_combo = '0' WHERE id = '{ctx.author}'"""
    )

  con_ids.commit()

  stats = cur_ids.execute(
    f"""SELECT points, combo, highest_combo FROM results WHERE id = '{ctx.author}'"""
  ).fetchall()

  results = cur_ids.execute(f"""SELECT id, points FROM results""").fetchall()
  dict_results = dict()
  for i in results:
    dict_results[i[0]] = int(i[1])

  sorted_keys = sorted(dict_results, key=dict_results.get, reverse=True)
  place_in_top = sorted_keys.index(str(ctx.author)) + 1

  if cur_lang == "ru":
    output = f"{ctx.author.mention} \
                \n**Количество очков**: *{stats[0][0]}*. \
                \n**Место в топе**: *{place_in_top}*. \
                \n**Комбо**: *{stats[0][1]}*. \
                \n**Макс. комбо**: *{stats[0][2]}*."

  else:
    output = f"{ctx.author.mention} \
                \n**Score**: *{stats[0][0]}*. \
                \n**Place in the top**: *{place_in_top}.* \
                \n**Combo**: *{stats[0][1]}*. \
                \n**Max. combo**: *{stats[0][2]}.*"

  await ctx.send(output)


@bot.command(name="countries")
async def countries(ctx, par=None):
  if str(ctx.author) not in [
      i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()
  ]:
    cur_ids.execute(
      f"""INSERT INTO options(id, language, timer, queue) VALUES('{ctx.author}', 'en', '15', 'None')"""
    )
    con_ids.commit()

  options = [
    i for i in cur_ids.execute(
      f"""SELECT language, timer FROM options WHERE id = '{ctx.author}'""").
    fetchall()[-1]
  ]
  cur_lang = options[0]

  queue = [
    i for i in cur_ids.execute(
      f"""SELECT id FROM options WHERE queue = 'taken'""").fetchall()
  ]
  if queue == [] or queue == [(str(ctx.author), )]:
    cur_ids.execute(
      f"""UPDATE options SET queue = 'taken' WHERE id = '{ctx.author}'""")
    con_ids.commit()
    bot.remove_command("reply")

    countries_list = cur_words.execute(
      f"""SELECT country, city FROM cities""").fetchall()

    right_cc = random.choice(countries_list)
    cities = [
      random.choice(countries_list)[1],
      random.choice(countries_list)[1], right_cc[1]
    ]
    random.shuffle(cities)

    if cur_lang == "ru":
      await ctx.reply(embed=discord.Embed(
        title=f'Выбери правильный вариант ответа!',
        description=f'\n Столицей страны {right_cc[0]} является... \
                                                \n**1.** {cities[0]}.\n**2.** {cities[1]}.\n**3**. {cities[2]}.',
        colour=discord.Color.dark_gray()))
    else:
      await ctx.reply(embed=discord.Embed(
        title=f'Choose the correct answer!',
        description=f'\n The capital of {right_cc[0]} is... \
                                                \n**1.** {cities[0]}.\n**2.** {cities[1]}.\n**3**. {cities[2]}.',
        colour=discord.Color.dark_gray()))

    def check(message):
      return message.author.id == ctx.author.id

    @bot.command()
    async def reply(ctx, answer):
      queue = [
        i for i in cur_ids.execute(
          f"""SELECT id FROM options WHERE queue = 'taken'""").fetchall()
      ]
      if queue == [(str(ctx.author), )]:
        if answer.isdigit():
          try:
            if cities[int(answer) - 1] == right_cc[1]:
              if cur_ids.execute(
                  f"""SELECT id FROM results WHERE id = '{ctx.author}'"""
              ).fetchall() == []:
                cur_ids.execute(
                  f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
                cur_ids.execute(
                  f"""UPDATE results SET points = '1', combo = '1', highest_combo = '1' WHERE id = '{ctx.author}'"""
                )
              else:
                combo = int(
                  cur_ids.execute(
                    f"""SELECT combo FROM results WHERE id = '{ctx.author}'"""
                  ).fetchall()[0][0]) + 1
                highest_combo = int(
                  cur_ids.execute(
                    f"""SELECT highest_combo FROM results WHERE id = '{ctx.author}'"""
                  ).fetchall()[0][0])
                cur_ids.execute(
                  f"""UPDATE results SET combo = '{combo}' WHERE id = '{ctx.author}'"""
                )
                if int(combo) > int(highest_combo):
                  cur_ids.execute(
                    f"""UPDATE results SET highest_combo = '{combo}' WHERE id = '{ctx.author}'"""
                  )

                points = int(
                  cur_ids.execute(
                    f"""SELECT points FROM results WHERE id = '{ctx.author}'"""
                  ).fetchall()[0][0])
                if combo < 10:
                  cur_ids.execute(
                    f"""UPDATE results SET points = '{points + 1}' WHERE id = '{ctx.author}'"""
                  )
                elif combo < 25:
                  cur_ids.execute(
                    f"""UPDATE results SET points = '{points + 2}' WHERE id = '{ctx.author}'"""
                  )
                elif combo >= 50:
                  cur_ids.execute(
                    f"""UPDATE results SET points = '{points + 3}' WHERE id = '{ctx.author}'"""
                  )

              con_ids.commit()

              await ctx.send("Верно!")
              if par == 'loop':
                asyncio.run_coroutine_threadsafe(countries(ctx, "loop"),
                                                 bot.loop)
              else:
                bot.remove_command("reply")
                cur_ids.execute(
                  f"""UPDATE options SET queue = 'None' WHERE id = '{ctx.author}'"""
                )
                con_ids.commit()
            else:
              if cur_ids.execute(
                  f"""SELECT id FROM results WHERE id = '{ctx.author}'"""
              ).fetchall() == []:
                cur_ids.execute(
                  f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
                cur_ids.execute(
                  f"""UPDATE results SET points = '0', combo = '0', highest_combo = '0' WHERE id = '{ctx.author}'"""
                )
              else:
                cur_ids.execute(
                  f"""UPDATE results SET combo = '0' WHERE id = '{ctx.author}'"""
                )

              if cur_lang == "ru":
                await ctx.send(
                  f"Ответ неверный! Правильный ответ - {right_cc[1]}.")
              else:
                await ctx.send(f"Wrong! Correct answer - {right_cc[1]}.")

              cur_ids.execute(
                f"""UPDATE options SET queue = 'None' WHERE id = '{ctx.author}'"""
              )
              con_ids.commit()
              bot.remove_command("reply")

          except IndexError:
            if cur_ids.execute(
                f"""SELECT id FROM results WHERE id = '{ctx.author}'"""
            ).fetchall() == []:
              cur_ids.execute(
                f"""INSERT INTO results(id) VALUES('{ctx.author}')""")
              cur_ids.execute(
                f"""UPDATE results SET points = '0', combo = '0', highest_combo = '0' WHERE id = '{ctx.author}'"""
              )
            else:
              cur_ids.execute(
                f"""UPDATE results SET combo = '0' WHERE id = '{ctx.author}'"""
              )
            if cur_lang == "ru":
              await ctx.send(
                f"Ответ неверный! Правильный ответ - **{right_cc[1]}**.")
            else:
              await ctx.send(f"Wrong! Correct answer - **{right_cc[1]}**.")

            bot.remove_command("reply")
            cur_ids.execute(
              f"""UPDATE options SET queue = 'None' WHERE id = '{ctx.author}'"""
            )
            con_ids.commit()
        else:
          if cur_lang == "ru":
            await ctx.reply(f'Ответ должен быть цифрой! Попробуйте ещё раз.')
          else:
            await ctx.reply(f'The answer must be a number! Try again.')

      else:
        if cur_lang == "ru":
          await ctx.reply(
            f"Ошибка! Пользователь **{queue[0][0]}** уже занимается!")
        else:
          await ctx.reply(
            f"Error! User **{queue[0][0]}** is already exercising")

    try:
      m = await bot.wait_for("message", check=check, timeout=int(options[1]))
    except asyncio.TimeoutError:
      bot.remove_command("reply")
      cur_ids.execute(
        f"""UPDATE options SET queue = 'None' WHERE id = '{ctx.author}'""")
      con_ids.commit()
      if cur_lang == "ru":
        await ctx.send(f"{ctx.author.mention} Время ответа вышло!")
      else:
        await ctx.send(f"{ctx.author.mention} Response time out!")
  else:
    if cur_lang == "ru":
      await ctx.reply(f"Ошибка! Пользователь **{queue[0][0]}** уже занимается!"
                      )
    else:
      await ctx.reply(f"Error! User **{queue[0][0]}** is already exercising")


@bot.command(name="help")
async def help(ctx, par='1'):
  if str(ctx.author) not in [
      i[0] for i in cur_ids.execute(f"""SELECT id FROM options""").fetchall()
  ]:
    cur_ids.execute(
      f"""INSERT INTO options(id, language, timer, queue) VALUES('{ctx.author}', 'en', '15', 'None')"""
    )
    con_ids.commit()

  options = [
    i for i in cur_ids.execute(
      f"""SELECT language, timer FROM options WHERE id = '{ctx.author}'""").
    fetchall()[-1]
  ]
  cur_lang = options[0]
  if cur_lang == "ru":
    if par == '1':
      output = '**Общие сведения о функциях бота.** \
            \n \
            \n**#** `/traducere [par] [spar]` - игра, целью которой является перевод предложенного слова с русского языка на английский и наоборот. Ответ:\
            \n`/reply [слово-перевод] [добавочное слово-перевод]`. \
            \n__Параметры__: _**loop**_ - зацикливание игрового процесса, _**en/ru**_ - выбор языка перевода. \
            \n \
            \n**#** `/words` - игра, целью которого является продолжение цепочки слов с последней буквы данного слова. Ответ:\
            \n`/reply [слово-продолжение].` \
            \n \
            \n**#**` /countries [par]` - игра, целью которой явлется проверка знаний названий столиц определенных знаний на английском языке. Ответ:\
            \n`/reply [цифра-ответ]` \
            \n__Параметры__: _**loop**_ - зацикливание игрового процесса. \
            \n \
            \n**#** `/cancel` - отмена ввода, например, при зацикленном вводе. \
            \n \
            \n*Для вывода следующего списка команд введите **"/help 2"***. '

    elif par == '2':
      output = "**#** `/timer [par] [spar]` - команда, изменяющая время ожидания, либо устаналивающая таймер на некоторое время.\
            \n_Параметры_: \
            \n **I.** _**[число]**_ - время, на которое будет установлен таймер _(до 300)_.\
            \n**II.** _**set**_ - указатель на следующий параметр, _**[число]**_ - время на ответ пользователя _(до 60)_.\
            \n***!**Без параметра выведет текущее значение времени ответа пользователя**!*** \
            \n \
            \n**#** `/language [par]` - команда, устанавливающая язык бота. \
            \n__Параметры__: _**ru/en**_ - язык, на котором будет отвечать бот. \
            \n***!**Без параметра выведет текущий установленный язык бота**!***\
            \n\
            \n**#** `/top [par]` - команда, выводящая локальный топ лидеров сервера по очкам. \
            \n__Параметры__: _**[число]**_ - число выводимых строк из списка лидеров. \
            \n\
            \n**#** `/statistic` - команда, выводящая общую статистику о человеке. "

    else:
      output = "/help может принимать в виде параметра только 1 и 2."

  else:
    if par == '1':
      output = '**General information about the functions of the bot.** \
            \n \
            \n**#** `/traducere [par] [spar]` - a game, the purpose of which is to translate the proposed word from Russian into English and vice versa. Reply:\
            \n`/reply [word] [additional translation]`. \
            \n__Parameters__: _**loop**_ - game looping, _**en/ru**_ - choice of translation language. \
            \n \
            \n**#** `/words` - a game whose goal is to continue a chain of words from the last letter of a given word. Reply:\
            \n`/reply [translation].` \
            \n \
            \n**#**` /countries [par]` - a game whose purpose is to test the knowledge of the names of the capitals of certain knowledge in English. Reply:\
            \n`/reply [digit]` \
            \n__Parameters__: _**loop**_ - game looping. \
            \n \
            \n**#** `/cancel` - cancellation of input, for example, with looped input. \
            \n \
            \n*To display the following list of commands, type **"/help 2"***. '

    elif par == '2':
      output = "**#** `/timer [par] [spar]` - a command that changes the waiting time, or sets the timer for a certain time.\
            \n__Parameters__: \
            \n **I.** _**[digit]**_ - time for which the timer will be set _(до 300)_.\
            \n**II.** _**set**_ - pointer to next parameter, _**[digit]**_ - user response time _(до 60)_.\
            \n***!**Without a parameter, will display the current value of the user's response time**!*** \
            \n \
            \n**#** `/language [par]` - command that sets the language of the bot. \
            \n__Parameters__: _**ru/en**_ - the language in which the bot will respond. \
            \n***!**Without parameter will display the currently installed language of the bot**!***\
            \n\
            \n**#** `/top [par]` - command that displays the local top of the server leaders by points. \
            \n__Parameters__: _**[digit]**_ - the number of rows to display from the leaderboard. \
            \n\
            \n**#** `/statistic` - command that displays general statistics about a person. "

    else:
      output = "/help может принимать в виде параметра только 1 и 2."

  await ctx.reply(output)


if __name__ == "__main__":
  bot.run(config.token)
