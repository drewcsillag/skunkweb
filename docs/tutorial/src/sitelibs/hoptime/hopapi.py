# Time-stamp: <02/11/12 09:08:19 smulloni> 

import PyDO
import sys
import mx.DateTime as M

def DEBUG(message):
    # at runtime in SkunkWeb, this method will
    # be replaced with a curried wrapper around
    # SkunkWeb.LogObj.DEBUG, but this
    # version enables the module to used
    # for testing/scripts
    print >> sys.stderr, message
    
# the connectstring when you aren't caching connections
# (for use outside the skunkweb daemon environment)
DEFAULT_CONNECTSTRING='pydo:postgresql:localhost:hoptime:postgres'

# what you use within skunkweb itself (w/ the postgresql service)
SW_CONNECTSTRING='pydo:postgresql:hoptime:cache'

def initDB(connectstring=DEFAULT_CONNECTSTRING, verbose=0):
    """
    this must be called before this module can be used.
    in skunkweb itself, it will get called during
    service initialization and therefore doesn't need to be
    called in templates or data components.
    """
    # in verbose mode, all SQL will be logged to stdout
    if verbose and not connectstring.endswith(':verbose'):
        connectstring+=':verbose'
    PyDO.DBIInitAlias('hoptime', connectstring)

class _hoptimebase(PyDO.PyDO):
    connectionAlias='hoptime'

class GameStateException(Exception): pass
class GameClosed(GameStateException): pass

# for convenience, reference these static methods
# outside of their purported owners
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

    def getUser(self):
        return Users.getUnique(id=self['player'])

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
            raise GameClosed
        Players.new(game=self['id'], player=user['id'])

    def getOwner(self):
        return Users.getUnique(id = self['owner'])

    def getPlayerForId(self, user_id):
        return Players.getUnique(game=self['id'], player=user_id)

    def getUsers(self):
        return self.joinTable('id',
                              "players",
                              'game',
                              'player',
                              Users,
                              'id')

    def getText(self, before_edit=0):
        # once play has ended, the resulting text is stored in the
        # stories table.
        if not before_edit and self['status'] in ('editing', 'published'):
            s=Stories.getUnique(game=self['id'])
            if s:
                return s['story']
            else:
                # shouldn't happen
                return None
        else:
            # to get the current text during play,
            # call a stored procedure that aggregates
            # it from the moves of the game.
            # No need to go through a PyDO object for this.
            sql='SELECT get_text(%d)' % self['id']
            c=getDBI().conn.cursor()
            c.execute(sql)
            t=c.fetchone()
            c.close()
            return t and t[0] or ""

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

    def getNextPlayerId(self):
        if self['status'] != 'playing':
            return None
        sql="SELECT get_next_turn(%s)" % self['id']
        c=getDBI().conn.cursor()
        c.execute(sql)
        u=c.fetchone()
        if u:
            return u[0]
        return None
    
    def getNextPlayer(self):
        id=self.getNextPlayerId()
        if id is not None:
            return Users.getUnique(id=id)


    def getMoveCount(self):
        sql="SELECT count(*) FROM moves where game=%s" % self['id']
        c=getDBI().conn.cursor()
        c.execute(sql)
        res=c.fetchone()
        return res and res[0] or 0

    def getMoves(self):
        return Moves.getSome(game=self['id'])

    def getLastMove(self):
        m=Moves.getSQLWhere("game=%d order by entered desc limit 1" % self['id'])
        return m and m[0] or None
           
        

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

    def getAllPlayedGames(self):
        return self.joinTable('id',
                              "players",
                              'player',
                              'game',
                              Games,
                              'id')

    def getAllPlayedButNotOwnedGames(self):
        sql="""SELECT %(fields)s FROM games g, players p
        WHERE players.player=%(user_id)s players.game=g.id
        AND g.owner!=%(user_id)s
        """ % {'fields' : ', '.join(['g.%s' % x for x in self.getColumns()]),
               'user_id' : self['id']}
        res=getDBI().conn.execute(sql, None, self.fieldDict)
        if not res:
            return None
        return map(self, res)


    def move(self, game, text):
        return Moves.new(refetch=1,
                         player=self['id'],
                         game=game['id'],
                         content_append=text)

    def fullName(self):
        return ' '.join(filter(None, [self['honorific'],
                                      self['firstname'],
                                      self['middlename'],
                                      self['lastname']]))


class Stories(_hoptimebase):
    table='stories'
    fields=(
        ('id', 'integer'),
        ('game', 'integer'),
        ('story', 'text'),
        ('published', 'timestamp'),
        )
    unique=[('id',), ('game',)]
    sequenced={
        'id' : 'stories_id_seq',
        }

    def getGame(self):
        return Games.getUnique(id=self['game'])


def getLatestStoryLinks(limit):
    sql="""
select s.id, g.title, s.published from stories s, games g
where s.game=g.id and g.status='published'
order by s.published desc limit %s
    """ % limit

    c=getDBI().conn.cursor()
    c.execute(sql)
    rows=c.fetchall()
    # manually convert the date to a datetime.
    # we could also use PyDO.postconn._dateConvertFromDB
    # instead of DateTimeFrom.
    return [[x, y, M.DateTimeFrom(z)] for x, y, z  in rows]

        
