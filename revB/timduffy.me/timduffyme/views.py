from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from .models import (
    DBSession,
    BlogModel,
    EventModel,
    )

import simplejson
import datetime

@view_config(route_name='/', renderer='templates/index.pt')
def home_view(request):
    return {}

@view_config(route_name="/blog", renderer='templates/blog.pt')
def blog_view(request):
    return {}

@view_config(route_name="/about", renderer='templates/about.pt')
def about_view(request):
    return {}

@view_config(route_name="/events.json", renderer='json')
def events_view(request):
    events = []
    _e = DBSession.query(EventModel).filter(EventModel.date >= datetime.datetime.now())
    for e in _e:
        events.append(e._json())
    return {"events":events}

@view_config(route_name="/posts.json", renderer='json')
def posts_view(request):
    posts = []
    _p = DBSession.query(BlogModel)
    for p in _p:
        posts.append(p._json())
    return {"posts":posts}



#@view_config(route_name='home', renderer='templates/mytemplate.pt')
#def my_view(request):
#    try:
#        one = DBSession.query(MyModel).filter(MyModel.name == 'one').first()
#    except DBAPIError:
#        return Response(conn_err_msg, content_type='text/plain', status_int=500)
#    return {'one': one, 'project': 'timduffy.me'}

conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_timduffy.me_db" script
    to initialize your database tables.  Check your virtual 
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

