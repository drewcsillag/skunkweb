# Time-stamp: <02/09/30 00:44:44 smulloni> 
# $Id: hoptime.py,v 1.1 2002/09/30 01:53:44 smulloni Exp $

import PyDO

DEFAULT_CONNECTSTRING='pydo:postgresql:localhost:hoptime:postgres'

def initDB(connectstring=DEFAULT_CONNECTSTRING):
    PyDO.DBIInitAlias('hoptime', connectstring)

class _hoptimebase(PyDO.PyDO):
    connectionAlias='hoptime'

class GameStateException(Exception): pass

rollback=_hoptimebase.rollback
commit=_hoptimebase.commit
getDBI=_hoptimebase.getDBI

class Players(_hoptimebase):
    table = 'players'
    fields = (
        ('player', 'integer'),
        ('game', 'integer'),
        ('joined', 'timestamp'),
        ('play_number', 'integer'),
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


class Moves(_hoptimebase):
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

class Games(_hoptimebase):
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
    unique = [('id',), ('title',)]

    sequenced = {
        'id': 'games_id_seq',
        }
    def getPlayers(self):
        return Players.getSome(game = self['id'])

    def addPlayer(self, user):
        if self['status']!='joining':
            raise "game closed"
        Players.new(game=self['id'], player=user['id'])

    def getOwner(self):
        return Users.getUnique(id = self['owner'])

    def getUsers(self):
        return self.joinTable('id',
                              "players",
                              'game',
                              'player',
                              Users,
                              'id')

    def getText(self, before_edit=0):
        if not before_edit and self['status'] in ('editing', 'published'):
            s=Stories.getUnique(game=self['id'])
            if s:
                return s['story']
            else:
                # shouldn't happen
                return None
        else:
            sql='SELECT get_text(%d)' % self['id']
            c=self.getDBI().conn.cursor()
            c.execute(sql)
            t=c.fetchone()
            c.close()
            return t

    def start(self):
        if self['status']=='joining':
            self['status']='playing'
        else:
            raise GameStateException, "game cannot be started"

    def edit(self):
        if self['status']=='playing':
            self['status']='editing'
        else:
            raise GameStateException, "game cannot be edited"

    def publish(self):
        if self['status'] in ('editing', 'playing'):
            self['status']='published'
        else:
            raise GameStateException, "game cannot be published"

    def trash(self):
        self['status']='trashed'
        

class Users(_hoptimebase):
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

    def move(self, game, text):
        return Moves.new(refetch=1, player=self['id'], game=game['id'], content_append=text)

class Stories(_hoptimebase):
    table='stories'
    fields=(
        ('id', 'integer'),
        ('game', 'integer'),
        ('story', 'text'),
        )
    unique=[('id',), ('game',)]
    sequenced={
        'id' : 'stories_id_seq',
        }

    def getGame(self):
        return Games.getUnique(id=self['game'])
