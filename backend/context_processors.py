def impersonation_context(request):
    """
    Adds the 'impersonator' object to the context if an impersonation
    session is active.
    """
    return {
        'impersonator': getattr(request, 'impersonator', None)
    }