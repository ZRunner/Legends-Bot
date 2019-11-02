from discord.ext import commands

class ClassesCog(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.data = list()
        self.file="classes"
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.get_data()


    async def get_data(self):
        cnx = self.bot.cnx
        cursor = cnx.cursor(dictionary=True)
        query = ("SELECT * FROM `classes` WHERE 1")
        cursor.execute(query)
        liste = list()
        for x in cursor:
            liste.append(x)
        cursor.close()
        self.data = liste
        return liste
    
    async def get_class(self,name):
        if len(self.data)==0:
            await self.get_data
        for x in self.data:
            if x['Name']==name:
                return x



def setup(bot):
    bot.add_cog(ClassesCog(bot))