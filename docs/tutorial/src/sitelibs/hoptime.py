# Time-stamp: <>
# $Id$

import PyDO
    
PyDO.DBIInitAlias('hoptime', 'pydo:postgresql:localhost:hoptime:postgres')

class Players(PyDO.PyDO):
    connectionAlias = 'hoptime'
    table = 'players'
    fields = (
        ('player', 'integer'),
        ('game', 'integer'),
        ('joined', 'timestamp'),
        ('play_number', 'integer')
    )
    unique = [('player', 'game')]

    def getGame(self):
        return Games.getUnique(id = self['game'])

    def getUser(self):
        return Users.getUnique(id = self['player'])

    def getEdits(self):
        return Edits.getSome(game = self['game'],
                             player = self['player'])

    def getMoves(self):
        return Moves.getSome(game = self['game'],
                             player = self['player'])


class Edits(PyDO.PyDO):
    connectionAlias = 'hoptime'
    table = 'edits'
    fields = (
        ('player', 'integer'),
        ('game', 'integer'),
        ('content_diff', 'text'),
        ('id', 'integer'),
        ('entered', 'timestamp'),
    )
    unique = [('id',)]

    sequenced = {
        'id': 'edits_id_seq',
    }
    def getPlayer(self):
        return Players.getUnique(player = self['player'],
                                 game=self['game'])

    def getUser(self):
        return Users.getUnique(id=self['player'])

    def getGame(self):
        return Games.getUnique(id=self['game'])

class Moves(PyDO.PyDO):
    connectionAlias = 'hoptime'
    table = 'moves'
    fields = (
        ('content_append', 'text'),
        ('player', 'integer'),
        ('game', 'integer'),
        ('entered', 'timestamp'),
        ('id', 'integer'),
    )
    unique = [('id',)]

    sequenced = {
        'id': 'moves_id_seq',
    }

class Games(PyDO.PyDO):
    connectionAlias = 'hoptime'
    table = 'games'
    fields = (
        ('owner', 'integer'),
        ('title', 'text'),
        ('description', 'text'),
        ('quorum', 'integer'),
        ('capacity', 'integer'), 
        ('status', 'varchar'),
        ('id', 'integer'),
        ('created', 'timestamp'),
    )
    unique = [('id',)]

    sequenced = {
        'id': 'games_id_seq',
    }
    def getPlayers(self):
        return Players.getSome(game = self['id'])

    def addPlayer(self, user):
        Players.new(game=self['id'], player=user['id'])

    def getOwner(self):
        return Users.getUnique(id = self['owner'])

    def getUsers(self):
        return self.joinTable('id', "players", 'game', 'player', Users, 'id')

class Users(PyDO.PyDO):
    connectionAlias = 'hoptime'
    table = 'users'
    fields = (
        ('username', 'text'),
        ('honorific', 'text'),
        ('firstname', 'text'),
        ('middlename', 'text'),
        ('lastname', 'text'),
        ('password', 'text'),
        ('id', 'integer'),
        ('email', 'text'),
    )
    unique = [('id',), ('username',)]

    sequenced = {
        'id': 'users_id_seq',
    }
    def getPlayers(self):
        return Players.getSome(player = self['id'])

    def getOwnedGames(self):
        return Games.getSome(owner = self['id'])

    def getPlayedGames(self):
        return self.joinTable('id', "players", 'player', 'game', Games, 'id')

