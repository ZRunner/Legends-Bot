import discord
import datetime
import time
from discord.ext import commands


# months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
#           "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Décembre"]


class TimeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.file = "timeclass"

    class timedelta:

        def __init__(self, years=0, months=0, days=0, hours=0, minutes=0, seconds=0, total_seconds=0, precision=2):
            self.years = years
            self.months = months
            self.days = days
            self.hours = hours
            self.minutes = minutes
            self.seconds = seconds
            self.total_seconds = total_seconds
            self.precision = precision

        def set_from_seconds(self):
            t = self.total_seconds
            rest = 0
            years, rest = divmod(t, 3.154e+7)
            months, rest = divmod(rest, 2.628e+6)
            days, rest = divmod(rest, 86400)
            hours, rest = divmod(rest, 3600)
            minutes, rest = divmod(rest, 60)
            seconds = rest
            self.years = int(years)
            self.months = int(months)
            self.days = int(days)
            self.hours = int(hours)
            self.minutes = int(minutes)
            if self.precision == 0:
                self.seconds = int(seconds)
            else:
                self.seconds = round(seconds, self.precision)

    async def time_delta(self, date1, date2, lang="fr", year=False, hour=True, digital=False, precision=2):
        """Traduit un intervale de deux temps datetime.datetime en chaine de caractère lisible"""
        delta = abs(date2 - date1)
        t = await self.time_interval(delta, precision)
        _ = self.bot._
        if digital:
            if hour:
                h = "{}:{}:{}".format(t.hours, t.minutes, t.seconds)
            else:
                h = ''
            text = '{}/{}{} {}'.format(t.days, t.months, "/"+str(t.years) if year else '', h)
        else:
            text = str()
            if year and t.years != 0:
                text += f"{t.years} {await _(lang, 'time.year', count=t.years)} "
            if t.months > 0:
                text += f"{t.months} {await _(lang, 'time.month', count=t.months)} "
            if t.days > 0:
                text += f"{t.days} {await _(lang, 'time.day', count=t.days)} "
            if hour:
                text += f"{t.hours} {await _(lang, 'time.hour', count=t.hours)} "
                text += f"{t.minutes} {await _(lang, 'time.minute', count=t.minutes)} "
                text += f"{t.seconds} {await _(lang, 'time.second', count=t.seconds)} "
        return text.strip()

    async def time_interval(self, tmd, precision=2):
        """Crée un objet de type timedelta à partir d'un objet datetime.timedelta"""
        t = tmd.total_seconds()
        obj = self.timedelta(total_seconds=t, precision=precision)
        obj.set_from_seconds()
        return obj

    async def date(self, date, lang='fr', year=False, hour=True, digital=False):
        """Traduit un objet de type datetime.datetime en chaine de caractère lisible. Renvoie un str"""
        if type(date) == time.struct_time:
            date = datetime.datetime(*date[:6])
        if type(date) == datetime.datetime:
            if len(str(date.day)) == 1:
                jour = "0"+str(date.day)
            else:
                jour = str(date.day)
            h = []
            for i in ['hour', 'minute', 'second']:
                a = getattr(date, i)
                if len(str(a)) == 1:
                    h.append("0"+str(a))
                else:
                    h.append(str(a))
            if digital:
                if date.month < 10:
                    month = "0"+str(date.month)
                else:
                    month = str(date.month)
                if lang == 'en':
                    df = "{m}/{d}{y}  {h}"
                else:
                    df = "{d}/{m}{y}  {h}"
                y = "/"+str(date.year) if year else ""
                h = ":".join(h) if hour else ""
                df = df.format(d=jour, m=month, y=y, h=h)
            else:
                if lang == 'en':
                    df = "{m} {d}, {y}  {h}"
                else:
                    df = "{d} {m} {y}  {h}"
                y = str(date.year) if year else ""
                h = ":".join(h) if hour else ""
                m = await self.bot._(lang, 'time.months')
                m = m[date.month-1]
                df = df.format(d=jour, m=m, y=y, h=h)
            return df


def setup(bot):
    bot.add_cog(TimeCog(bot))
