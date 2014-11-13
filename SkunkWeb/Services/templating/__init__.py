#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

# load web and ae_component services, upon which templating depends.
import web 
import ae_component

def __initFlag():
    from SkunkWeb import ServiceRegistry
    ServiceRegistry.registerService('templating')

def __initTags():
    from AE.Cache import tagRegistry
    import ArgsTag
    tagRegistry.addTag(ArgsTag.ArgsTag())
    import LogTags
    for i in LogTags.LoggingTags:
        tagRegistry.addTag(i)
    import SendmailTag
    tagRegistry.addTag(SendmailTag.SendmailTag())
    import HTMLTags
    for i in ['UrlTag', 'ImageTag', 'FormTag', 'HiddenTag', 'RedirectTag']:
        tagRegistry.addTag(getattr(HTMLTags, i)())
    import SafeSpoolTag
    tagRegistry.removeTag('spool')
    tagRegistry.addTag(SafeSpoolTag.SafeSpoolTag())
    
def _formatException(exc_text, sessionDict):
    return exc_text

def __initHooks():
    import SkunkWeb.constants as skc
    import Handler
    from web.protocol import HandleConnection
    from requestHandler.protocol import RequestFailed
    jobGlob=skc.TEMPLATING_JOB+'*'
    HandleConnection.addFunction(Handler.requestHandler, jobGlob)
    HandleConnection.addFunction(Handler.plainHandler, jobGlob)
    HandleConnection.addFunction(Handler.fourOhFourHandler, jobGlob)
    RequestFailed.addFunction(_formatException, jobGlob)
    import SkunkWeb.Configuration
    SkunkWeb.Configuration.mergeDefaults(job=skc.TEMPLATING_JOB)


########################################################################

__initFlag()
__initHooks()
__initTags()

import SkunkWeb.LogObj
SkunkWeb.LogObj.LOG("templating service loaded")

