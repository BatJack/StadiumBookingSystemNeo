"""
Context processors for the booking app.

Context processors automatically inject variables into all template contexts.
This is more efficient than manually passing the same variables in every view.
"""


def background_defaults(request):
    """
    Inject default background image filename into all template contexts.
    
    Returns a constant dict — no I/O, no database queries, just a string.
    Templates can use {{ BG_DEFAULT_FILE }} directly.
    """
    return {'BG_DEFAULT_FILE': 'login.jpg'}
