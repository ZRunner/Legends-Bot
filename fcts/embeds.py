import datetime
import nextcord
import requests
from nextcord.ext import commands

base_url = "https://discordapp.com/api/webhooks/513473320268726322/"

def getIfromRGB(rgb):
    red = rgb[0]
    green = rgb[1]
    blue = rgb[2]
    RGBint = (red << 16) + (green << 8) + blue
    return RGBint


class EmbedCog(commands.Cog):
    """Cog for the management of the embeds. No more, no less."""

    def __init__(self, bot):
        self.bot = bot
        self.logs = base_url + "a4qc8NbVyymrhjZEvojRDiyniK67VLInWomMNrInTB-0_yh1Bko0rhx1rIUeSpTGWaFY"
        self.file = "embeds"

    class Embed:
        def __init__(self, content="", title="", desc="", url="", color=0, time=nextcord.Embed.Empty, footer_url="", footer_text="", thumbnail="", image="", author_name="", author_url="", author_icon="", fields=[]):
            self.content = content
            self.title = title
            self.description = desc
            self.url = url
            self.color = color if type(
                color) == int else getIfromRGB(color.to_rgb())
            self.timestamp = time
            self.footer_text = footer_text
            self.footer_url = footer_url
            self.thumbnail = thumbnail
            self.image = image
            self.author_name = author_name
            self.author_url = author_url
            self.author_icon = author_icon
            self.fields = fields
            for x in self.fields:
                if "inline" not in x.keys():
                    x['inline'] = False
                if "name" not in x.keys():
                    x["name"] = "No name"
                if "value" not in x.keys():
                    x["value"] = "No value"

        def update_timestamp(self):
            self.timestamp = datetime.datetime.now(datetime.timezone.utc)
            return self

        def json(self):
            j = dict()
            emb = dict()
            if self.title != "":
                emb["title"] = self.title
            if self.description != "":
                emb["description"] = self.description
            if self.url != "":
                emb["url"] = self.url
            if self.color != 0:
                emb["color"] = self.color
            if self.timestamp != nextcord.Embed.Empty:
                emb["timestamp"] = str(self.timestamp)
            if self.footer_text != "" and self.footer_url != "":
                emb["footer"] = {"icon_url": self.footer_url,
                                 "icon_text": self.footer_text}
            if self.thumbnail != "":
                emb["thumbnail"] = {"url": self.thumbnail}
            if self.image != "":
                emb["image"] = {"url": self.image}
            if self.author_icon != "" or self.author_name != "" or self.author_url != "":
                auth = dict()
                if self.author_name != "":
                    auth["name"] = self.author_name
                if self.author_url != "":
                    auth["url"] = self.author_url
                if self.author_icon != "":
                    auth["icon_url"] = self.author_icon
                emb["author"] = auth
            if self.fields != []:
                emb["fields"] = self.fields
            if emb != {}:
                j["embed"] = emb
            if self.content != "":
                j["content"] = self.content
            return j
        
        def to_dict(self):
            return self.json()['embed']

        def set_author(self, user: nextcord.User):
            self.author_name = user.name
            self.author_icon = user.display_avatar.with_format('png').url
            return self

        def create_footer(self, user: nextcord.User):
            self.footer_text = "Requested by "+user.name
            self.footer_url = user.display_avatar.with_format('png').url
            return self

        def discord_embed(self):
            emb = nextcord.Embed(title=self.title, colour=nextcord.Color(
                self.color), url=self.url, description=self.description, timestamp=self.timestamp)
            emb.set_image(url=self.image)
            emb.set_thumbnail(url=self.thumbnail)
            emb.set_author(name=self.author_name,
                           url=self.author_url, icon_url=self.author_icon)
            emb.set_footer(text=self.footer_text, icon_url=self.footer_url)
            for x in self.fields:
                emb.add_field(name=x["name"],
                              value=x["value"], inline=x["inline"])
            return emb

    async def send(self, embeds, url=None, ctx=None):
        if url == None:
            url = self.logs
        liste = list()
        for x in embeds:
            if type(x) == self.Embed:
                liste.append(x.json()["embed"])
            else:
                liste.append(x["embed"])
        r = requests.post(url, json={"embeds": liste})
        if ctx != None:
            try:
                msg = eval(r.text)
                if "message" in msg.keys():
                    msg = msg["message"]
                elif "_misc" in msg.keys():
                    msg = msg["_misc"][0]
            except:
                return
            await ctx.send("`Erreur {}:` {}".format(r.status_code, msg))


def setup(bot):
    bot.add_cog(EmbedCog(bot))
