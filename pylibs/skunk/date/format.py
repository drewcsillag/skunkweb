import time

def HTTPDate(secs=None):
    """
    Returns a DateString object with format set to RFC 1123,
    for use by code needing to return dates in the format expected
    in email, web, or other net-based formats. This format corresponds
    to the Unix strftime format: 
    '%a, %d %b %Y %H:%M:%S GMT'
    This function is used by the SkunkWeb server to make
    date strings extra quickly.
    """
    if secs==None:
        secs=time.time()
    return time.strftime('%a, %d %b %Y %H:%M:%S GMT',
                         time.gmtime(secs))
