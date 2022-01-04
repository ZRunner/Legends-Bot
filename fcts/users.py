import random
from nextcord.ext import commands

class UsersCog(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.file = "users"
        self.data = dict()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.get_data()

    async def generate_id(self):
        liste = list()
        for x in self.data.keys():
            liste.append(int(x))
        return max(liste)+1
    
    async def user_has_perso(self,userID,perso):
        deck = await self.get_user_deck(userID)
        for x in deck:
            if x['personnage']==perso:
                return True
        return False

    async def get_user_deck(self,userID:int,IDonly:bool=False):
        """Retourne la liste des personnages obtenus par un joueur"""
        cnx = self.bot.cnx
        cursor = cnx.cursor(dictionary=True)
        query = ("SELECT * FROM `users` WHERE `userID`={}".format(userID))
        cursor.execute(query)
        if IDonly:
            d = list()
        else:
            d = dict()
        persos = await self.bot.cogs['PersosCog'].get_names_list()
        for x in cursor:
            if x['personnage'] in persos:
                if IDonly:
                    d.append(x['ID'])
                else:
                    d[x['ID']] = x
        cursor.close()
        return d

    async def get_data(self):
        """Retourne la liste de tous les personnages obtenus"""
        cnx = self.bot.cnx
        cursor = cnx.cursor(dictionary=True)
        query = ("SELECT * FROM `users` WHERE 1")
        cursor.execute(query)
        d = dict()
        for x in cursor:
            d[x['ID']] = x
        cursor.close()
        self.data = d
        return d
    
    async def add_perso(self,perso,userID,level=1,morts=0):
        """Ajoute un personnage à un joueur"""
        cnx = self.bot.cnx
        cursor = cnx.cursor()
        datas = await self.get_data()
        ID = max([x['ID'] for x in datas.values()])+1
        query = ("INSERT INTO `users` (`ID`, `userID`, `personnage`, `level`, `date`, `morts`) VALUES ('{}', '{}', '{}', '{}', CURRENT_TIMESTAMP, '{}'); ".format(ID,userID,perso,level,morts))
        cursor.execute(query)
        cnx.commit()
        cursor.close()
        return True
    
    async def remove_perso(self,persoID,userID):
        """Supprime de la base de donnée un personnage"""
        if type(persoID)!=int or type(userID)!=int:
            raise ValueError
        cnx = self.bot.cnx
        cursor = cnx.cursor()
        query = ("DELETE FROM `users` WHERE `ID`='{}' AND `userID`='{}'".format(persoID,userID))
        cursor.execute(query)
        cnx.commit()
        cursor.close()
        return True

    
    async def reset_player(self,userID):
        """Enlève à un joueur tout ses personnages"""
        c = 0
        persos = await self.get_user_deck(userID)
        for p in persos.values():
            await self.remove_perso(p['ID'],userID)
            c += 1
        return c

    async def select_starterKit(self,user):
        """Attribue 5 personnages aléatoires à l'utilisateur"""
        datas = await self.bot.cogs['PersosCog'].get_data()
        liste = [x for x in datas.values() if x['actif']]
        selected = list()
        for _ in range(5):
            selected.append(random.choice(liste))
            await self.add_perso(selected[-1]['Name'],user.id)
            liste.remove(selected[-1])
        return [x['Name'] for x in selected]



def setup(bot):
    bot.add_cog(UsersCog(bot))