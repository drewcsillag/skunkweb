
def _hook(*args, **kwargs):
    try:
        import psyco
    except ImportError:
        pass
    else:
        psyco.profile()


from SkunkWeb.Hooks import ChildStart
ChildStart.append(_hook)
del ChildStart

    
