import hoptime
hoptime.initDB(hoptime.DEFAULT_CONNECTSTRING+":verbose")

def initUsers():
    smulloni=hoptime.Users.new(refetch=1,
                               username='smulloni',
                               email='smulloni@smullyan.org',
                               firstname='Jacob',
                               lastname='Smullyan',
                               password='hoptime')
    alvin=hoptime.Users.new(refetch=1,
                            username='alvin',
                            email='alvin@krinst.org',
                            firstname='Alvin',
                            lastname='Krinst',
                            password='hoptime')
    fafnir=hoptime.Users.new(refetch=1,
                             username='fafnir',
                             email='fafnir@krinst.org',
                             firstname='Fafnir',
                             lastname='Finkelmeyer',
                             password='hoptime')

def prepareGame():
    smulloni=hoptime.Users.getUnique(username='smulloni')
    fafnir=hoptime.Users.getUnique(username='fafnir')
    alvin=hoptime.Users.getUnique(username='alvin')
    game=hoptime.Games.new(refetch=1,
                           title='Rancid Rodents',
                           description='Lots of Smelly Vermin Everywhere',
                           owner=alvin['id'])
    game.addPlayer(smulloni)
    game.addPlayer(fafnir)
    game.start()

def playGame():
    smulloni=hoptime.Users.getUnique(username='smulloni')
    fafnir=hoptime.Users.getUnique(username='fafnir')
    alvin=hoptime.Users.getUnique(username='alvin')
    game=hoptime.Games.getUnique(title='Rancid Rodents')
    alvin.move(game, "Bozo wept.  ")
    smulloni.move(game, "Bunko crept into his soul like a chigger; ")
    fafnir.move(game, "no one named Grace was allowed near or ")
    alvin.move(game, "to bear his company.")

    print game.getText()
    

def publishGame():
    game=hoptime.Games.getUnique(title='Rancid Rodents')
    game.publish()
    

