import simplejson

from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    DateTime,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class BlogModel(Base):
    __tablename__ = 'blogs'
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    posted = Column(DateTime)
    content = Column(Text)

    def __init__(self,title,posted,content):
       self.title = title
       self.posted = posted
       self.content = content

    def _json(self):
       return {
           "id"      : self.id,
           "title"   : self.title.encode('utf-8'),
           "posted"  : self.__prettydatetime().encode('utf-8'),
           "content" : self.content.encode('utf-8')
       }

    def __prettydatetime(self):
        if self.posted is None:
            return None
        return "{0} at {1}".format(self.posted.strftime("%Y-%m-%d"), self.posted.strftime("%H:%M:%S"))


class EventModel(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    title = Column(Text)
    url = Column(Text)

    def __init__(self,date,title,url):
        self.date = date
        self.title = title
        self.url = url

    def _json(self):
        return {
            "id"    : self.id,
            "date"  : self.__prettydate(),
            "title" : self.title.encode("utf-8"),
            "url"   : self.url.encode("utf-8")
        }

    def __prettydate(self):
        if self.date is None:
            return None
        return "{0}".format(self.date.strftime("%Y-%m-%d"))


#class MyModel(Base):
#    __tablename__ = 'models'
#    id = Column(Integer, primary_key=True)
#    name = Column(Text)
#    value = Column(Integer)
#
#    def __init__(self, name, value):
#        self.name = name
#        self.value = value
#
#Index('my_index', MyModel.name, unique=True, mysql_length=255)
