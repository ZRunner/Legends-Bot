#!/usr/bin/env python
#coding=utf-8

import sys
import time

t1 = time.time()

# check python version
py_version = sys.version_info
if py_version.major != 3 or py_version.minor < 9:
    print("You must use at least Python 3.9!", file=sys.stderr)
    sys.exit(1)

import pkg_resources


def check_libs():
    """Check if the required libraries are installed and can be imported"""
    with open("requirements.txt", 'r') as file:
        packages = pkg_resources.parse_requirements(file.readlines())
    pkg_resources.working_set.resolve(packages)


check_libs()

import os
import traceback
import nextcord
from utils import LegendsBot, setup_logger

initial_extensions = ['fcts.admin',
                    'fcts.commands',
                    'fcts.errors',
                    'fcts.languages',
                    'fcts.persos',
                    'fcts.reloads',
                    'fcts.timeclass',
                    'fcts.users',
                    'fcts.utilities',
                    'fcts.aide',
                    'fcts.embeds',
                    'fcts.attacks',
                    'fcts.effects'
  ]

def main():
    client = LegendsBot(case_insensitive=True, status=nextcord.Status('online'))
    if os.path.exists("debug.log"):
        s = os.path.getsize('debug.log')/1.e9
        if s > 2:
            print("Taille de debug.log supérieure à 2Gb ({}Gb)\n   -> Suppression des logs".format(s))
            os.remove('debug.log')
        del s

    # Here we load our extensions(cogs) listed above in [initial_extensions]
    count = 0
    for extension in initial_extensions:
        try:
            client.load_extension(extension)
        except:
            print(f'\nFailed to load extension {extension}', file=sys.stderr)
            traceback.print_exc()
            count += 1
        if count >0:
            raise Exception("\n{} modules not loaded".format(count))
    del count

    async def on_ready():
        await client.get_cog("UtilitiesCog").count_lines_code()
        print('\nBot connecté')
        print("Nom : "+client.user.name)
        print("ID : "+str(client.user.id))
        serveurs = []
        for i in client.guilds:
            serveurs.append(i.name)
        ihvbsdi="Connecté sur ["+str(len(client.guilds))+"] "+", ".join(serveurs)
        print(ihvbsdi)
        print(time.strftime("%d/%m  %H:%M:%S"))
        print("Prêt en {}s".format(round(time.time()-t1,3)))
        print('------')
        await client.change_presence(activity=nextcord.Game(name="baaatttle!"))

    with open('secrets.txt','r') as f:
        token = f.read().strip()

    client.add_listener(on_ready)

    log = setup_logger()
    log.info("Lancement du bot")

    client.run(token)


if __name__ == "__main__":
    main()
