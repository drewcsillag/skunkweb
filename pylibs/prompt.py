#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
A prompt module, useful for asking interactive questions.
It's fairly simple, and generally for use in command-line
tools, not web applications. Enjoy.
"""

import string
import sys

class Question:
    """The father of all Question subclasses"""
    def __init__ ( self, quest, default = None ):
        """Setup a question"""
        self._quest = quest
        self._default = default

        # Answer
        self._answer = None

    def setDefault ( self, val ):
        """set a default so if they don't answer, they get this"""
        self._default = val

    def set ( self, a ):
        """force an answer"""
        self._answer = a

    def ask ( self, convert = lambda x:x ):
        """ 
        Ask the question until an answer is given
        """
        while 1:
            ans = self.ask_quest()

            if None == ans:
                continue

            self._answer = convert(ans)
            break
        return self._answer

    def ask_quest ( self ):
        """
        Ask a question once, returning None on incorrect answer
        """
        raise NotImplementedError

    def get ( self ):
        """
        Get the value of self
        """
        if None == self._answer:
            return self._default
        else:
            return self._answer 

class CharQuestion(Question):
    """
    Ask a single character question
    """
    def __init__ ( self, quest, allowed, defchar = None ):
        """construct the question with the prompt string quest,
        the set of allowed responses allowed and the default response
        defchar"""
        
        Question.__init__ ( self, quest, defchar )
        self._allowed = string.lower(allowed)

        # Check sanity
        if self._default not in self._allowed:
             raise ValueError, 'not a valid character: %s' % self._default

    def ask_quest ( self ):
        """
        Ask the question, return the char the user chose.
        """
        vals = list ( self._allowed )
        for i in range ( 0, len(vals) ):
             if vals[i] == self._default:
                 vals[i] = string.upper(vals[i])
       
        astr = string.join ( vals, '/' )

        sys.stdout.write ( '%s? [%s] ' % ( self._quest, astr ))
        sys.stdout.flush()

        ret = string.lower(string.strip(sys.stdin.readline()))

        if not ret:
             # Use default
             ret = self._default
        elif len(ret) > 1:
             print ( 'Single character expected' )
             ret = None
        elif ret not in self._allowed:
             print ( 'Answer has to be one of [%s]' % astr )
             ret = None

        return ret

class BoolQuestion(CharQuestion):
    """
    A boolean question
    """
    def __init__(self, quest, default = None ):
        """
        Default is boolean true or false, i.e. 1 or 0, quest is the
        prompt string.
        """
        if default:
            defchar = 'y'
        else:
            defchar = 'n'

        CharQuestion.__init__ ( self, quest, 'yn', defchar )

    def ask_quest(self):
        """
        Ask the question, return 1 if yes, 0 if no
        """
        ret = CharQuestion.ask_quest ( self )

        # Return boolean
        return ret == 'y' 

class StringQuestion(Question):
    """
    Asks a freeform string question
    """
    def __init__ ( self, quest, default = None ):
        """Init a string question"""
        Question.__init__ ( self, quest, default )

    def ask_quest ( self ):
        """Ask a string question, returns the response"""
        df = self._default or ''
        sys.stdout.write ( '%s? [%s] ' % ( self._quest, df ))
        sys.stdout.flush()

        ret = string.strip(sys.stdin.readline())

        return ret or df
