###Dispatcher Database Design###

I am a big fan of writing SQL to interface to and design the database.  This is why I wrote [sql2api](https://github.com/thequbit/sql2api).  The tool allows you to write SQL to define a MySQL database and from that generate a python object-based interface to the database.

I spoke briefly about using [SQLAlchemy](http://www.sqlalchemy.org/) with BarkingOwl in this [post](http://timduffy.me/posts/syracuse_hacks_and_hackers_meetup.html).  I've played a bit with the library since writing that post, and I just am not a fan of it.  Now I do believe one of the main reasons for this was my rather limit understanding of Python and my limited object oriented programming experience.  Plus, I like SQL so removing myself from that portion of the database doesn't really make sense to me :p.

First, let's design some tables:

    CREATE TABLE IF NOT EXISTS urls(
        urlid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        targeturl TEXT NOT NULL,
        maxlinklevel INT NOT NULL,
        creationdatetime DATETIME NOT NULL,
        doctypeid INT NOT NULL,
        FOREIGN KEY (doctypeid) REFERENCES doctypes(doctypeid)
    );

    CREATE INDEX urls_urlid ON urls(urlid);

    CREATE TABLE IF NOT EXISTS doctypes(
        doctypeid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        title CHAR(256) NOT NULL,
        description TEXT NOT NULL,
        doctype CHAR(256) NOT NULL
    );

    CREATE INDEX doctypes_doctypeid ON doctypes(doctypeid);
    CREATE INDEX doctypes_doctype ON doctypes(doctype);

What we have here are two tables that hold enough information to get a basic Dispatcher up and running.  Let's take a look at what we have.

  - **urls**
    - urlid
      - The unique ID of the row in the urls table.  This will be important as it will be unique to each URL within the BarkingOwl instance.
    - targeturl
      - This is the URL that the Scraper should scrape (ex. 'http://www.townofchili.org/')
    - maxlinklevel
      - This is the maximum number of links to follow.  From what I have seen levels of more than 3 can become extremely large bandwidth and can consume a LOT of time.  In some of my tests that I ran I saw as many as 50,000 links followed when setting the level of 5 on a SINGLE URL.
    - creationdatetime
      - The Date and Time of when the URL entry was entered in the Database.
    - doctypeid
      - This is the ID in the other table in the Database.
      - This is the type of the document that the Scraper should be looking for while scraping.  We will be doing a JOIN within the SQL query to get this data into a single response.

  - **doctypes**
    - doctypeid
      - The unique ID of the row in the doctypes table.  This is referenced by the **urls** table.
    - title
      - A Title for the document type.  An example would be 'Adobe PDF'.
    - description
      - A brief description of the document type (specifically useful if the doc type is not a well known standard, or preparatory).
    - doctype
      - The actual document type.  This will be the exact text that is returned by the magic library.  An example would be 'application/pdf'.

Now that we have the tables defined, and we know what each part does, we can push the SQL into the sql2api tool.

Note: I added these two files at the beginning of the database creation script so the sql2api tool knows what the Database is called and it can be used right by MySQL.

    CREATE DATABASE IF NOT EXISTS bodisparcherdb;
    USE bodisparcherdb;

Now, let's pass the file into the sql2api tool:

    $ python sql2api.py dispatcher.sql
    [INFO] Parsing SQL ...
    [INFO] Database Name: bodisparcherdb
    [INFO] Found Table: `urls` with 5 columns
    [INFO] Found Table: `doctypes` with 4 columns
    [INFO] Generating Python Files ...
    [INFO]  ./bodisparcherdb/python/models/__dbcreds__.py
    [INFO]  ./bodisparcherdb/python/models/Urls.py
    [INFO]  ./bodisparcherdb/python/models/Doctypes.py
    [INFO]  ./bodisparcherdb/python/models/__init__.py
    [INFO] Generating PHP Files ...
    [INFO]  ./bodisparcherdb/php/UrlsManager.class.php
    [INFO]  ./bodisparcherdb/php/DoctypesManager.class.php
    [INFO]  ./bodisparcherdb/php/sqlcredentials.php
    [INFO]  ./bodisparcherdb/php/getall.php

    Application exiting ...

You will notice that, at least using the version of the tool that was available at the time of this blog post, that sql2api spits out python as well as PHP code.  We will only be using the Python code for the Dispatcher.

Let's take a look at the files that were created.  First, the file system tree that was created was:

    bodisparcherdb/
      python/
        models/
          __dbcreds__.py
          Urls.py
          Doctypes.py
          __init__.py

The four files that are created are described as below:

  - __dbcreds__.py
    - This holds the database credentials.  This holds four variables
      - __username__ = '' # the username for the MySQL database
      - __password__ = '' # the password for the MySQL database
      - __database__ = '' # the name of the database, here it is bodispatcherdb
      - __server__ = '' # this is the server name or IP address
  - Urls.py
    - This holds the class that allows access to the **urls** table
  - Doctypes.py
    - This holds the class that allows access to the **doctypes** table
  - __init__.py
    - This is called when the calling python script imports the directory that all of these files are in.
    - This tries to connect to the database using the credentials, and initializes the classes that allow access to the tables in the database.

Let's quickly look at how we would go about using the created tables.

    from models import *

    def geturls():
        urls = Urls()
        urllist = urls.getall()
        return urllist

    def printurls(urllist):
        for url in urls:
            # urlid,targeturl,maxlinklevel,creationdatetime,doctypeid = url
            print url
                
    
    def main():
        urllist = geturls()
        printurls(urllist)

    main()

The above code will import the models created by sql2api, and allow access to the Urls class which, in turn, allows access to the Urls table within the MySQL database.  The getall() function is built into each class generated by sql2api by default.  The printurls() function then just iterates through and prints all of the information from the row in the Database.  Note how each tuple in the array holds 5 items (the same 5 items that are in the table).

###Creating a New Database Accesser

Since it's impossible for the sql2api to know all of way queries we want to perform, as we come up with them we need to add Accessor.  Luckily sql2api places a nice little template at the end of each file it creates on how to add an Accessor, there for creating one is simple!

First, we need to define our query with the JOIN so we can get the information from both tables into a single response.

    SELECT
      urls.urlid as urlid,
      urls.targeturl as targeturl,
      urls.maxlinklevel as maxlinklevel,
      urls.creationdatetime as creationdatetime,
      doctypes.title as doctypetitle,
      doctypes.description as docdescription,
      doctypes.doctype as doctype
    FROM 
      urls 
    JOINI am a big fan of writing SQL to interface to and design the database.  This is why I wrote [sql2api](https://github.com/thequbit/sql2api).  The tool allows you to write SQL to define a MySQL database and from that generate a python object-based interface to the database.

I spoke briefly about using [SQLAlchemy](http://www.sqlalchemy.org/) with BarkingOwl in this [post](http://timduffy.me/posts/syracuse_hacks_and_hackers_meetup.html).  I've played a bit with the library since writing that post, and I just am not a fan of it.  Now I do believe one of the main reasons for this was my rather limit understanding of Python and my limited object oriented programming experience.  Plus, I like SQL so removing myself from that portion of the database doesn't really make sense to me :p.

###Dispatcher Database Design###

First, let's design some tables:

    CREATE TABLE IF NOT EXISTS doctypes(
        doctypeid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        title CHAR(256) NOT NULL,
        description TEXT NOT NULL,
        doctype CHAR(256) NOT NULL
    );

    CREATE INDEX doctypes_doctypeid ON doctypes(doctypeid);
    CREATE INDEX doctypes_doctype ON doctypes(doctype);

    CREATE TABLE IF NOT EXISTS urls(
        urlid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        targeturl TEXT NOT NULL,
        maxlinklevel INT NOT NULL,
        creationdatetime DATETIME NOT NULL,
        doctypeid INT NOT NULL,
        FOREIGN KEY (doctypeid) REFERENCES doctypes(doctypeid)
    );

    CREATE INDEX urls_urlid ON urls(urlid);

What we have here are two tables that hold enough information to get a basic Dispatcher up and running.  Let's take a look at what we have.

  - **urls**
    - urlid
      - The unique ID of the row in the urls table.  This will be important as it will be unique to each URL within the BarkingOwl instance.
    - targeturl
      - This is the URL that the Scraper should scrape (ex. 'http://www.townofchili.org/')
    - maxlinklevel
      - This is the maximum number of links to follow.  From what I have seen levels of more than 3 can become extremely large bandwidth and can consume a LOT of time.  In some of my tests that I ran I saw as many as 50,000 links followed when setting the level of 5 on a SINGLE URL.
    - creationdatetime
      - The Date and Time of when the URL entry was entered in the Database.
    - doctypeid
      - This is the ID in the other table in the Database.
      - This is the type of the document that the Scraper should be looking for while scraping.  We will be doing a JOIN within the SQL query to get this data into a single response.

  - **doctypes**
    - doctypeid
      - The unique ID of the row in the doctypes table.  This is referenced by the **urls** table.
    - title
      - A Title for the document type.  An example would be 'Adobe PDF'.
    - description
      - A brief description of the document type (specifically useful if the doc type is not a well known standard, or preparatory).
    - doctype
      - The actual document type.  This will be the exact text that is returned by the magic library.  An example would be 'application/pdf'.

###Create Database Accessers Using sql2api### 

Now that we have the tables defined, and we know what each part does, we can push the SQL into the sql2api tool.

Note: I added these two files at the beginning of the database creation script so the sql2api tool knows what the Database is called and it can be used right by MySQL.

    CREATE DATABASE IF NOT EXISTS bodisparcherdb;
    USE bodisparcherdb;

Now, let's pass the file into the sql2api tool:

    $ python sql2api.py dispatcher.sql
    [INFO] Parsing SQL ...
    [INFO] Database Name: bodisparcherdb
    [INFO] Found Table: `urls` with 5 columns
    [INFO] Found Table: `doctypes` with 4 columns
    [INFO] Generating Python Files ...
    [INFO]  ./bodisparcherdb/python/models/__dbcreds__.py
    [INFO]  ./bodisparcherdb/python/models/Urls.py
    [INFO]  ./bodisparcherdb/python/models/Doctypes.py
    [INFO]  ./bodisparcherdb/python/models/__init__.py
    [INFO] Generating PHP Files ...
    [INFO]  ./bodisparcherdb/php/UrlsManager.class.php
    [INFO]  ./bodisparcherdb/php/DoctypesManager.class.php
    [INFO]  ./bodisparcherdb/php/sqlcredentials.php
    [INFO]  ./bodisparcherdb/php/getall.php

    Application exiting ...

You will notice that, at least using the version of the tool that was available at the time of this blog post, that sql2api spits out python as well as PHP code.  We will only be using the Python code for the Dispatcher.

Let's take a look at the files that were created.  First, the file system tree that was created was:

    bodisparcherdb/
      python/
        models/
          __dbcreds__.py
          Urls.py
          Doctypes.py
          __init__.py

The four files that are created are described as below:

  - __dbcreds__.py
    - This holds the database credentials.  This holds four variables
      - __username__ = '' # the username for the MySQL database
      - __password__ = '' # the password for the MySQL database
      - __database__ = '' # the name of the database, here it is bodispatcherdb
      - __server__ = '' # this is the server name or IP address
  - Urls.py
    - This holds the class that allows access to the **urls** table
  - Doctypes.py
    - This holds the class that allows access to the **doctypes** table
  - __init__.py
    - This is called when the calling python script imports the directory that all of these files are in.
    - This tries to connect to the database using the credentials, and initializes the classes that allow access to the tables in the database.

###Create Database and Tables in MySQL###

Now that we have the Access Classes generated, we can create the database within our MySQL instance.

    # mysql -u root -p < dispatcher.sql

    # mysql -u root -p  
    mysql> use bodispatcherdb;
    mysql> grant usage on bodispatcherdb.* to bouser identified by '<password>';
    mysql> grant all privileges on bodispatcherdb.* to bouser;
    mysql> show columns from urls;
    +------------------+----------+------+-----+---------+----------------+
    | Field            | Type     | Null | Key | Default | Extra          |
    +------------------+----------+------+-----+---------+----------------+
    | urlid            | int(11)  | NO   | PRI | NULL    | auto_increment |
    | targeturl        | text     | NO   |     | NULL    |                |
    | maxlinklevel     | int(11)  | NO   |     | NULL    |                |
    | creationdatetime | datetime | NO   |     | NULL    |                |
    | doctypeid        | int(11)  | NO   | MUL | NULL    |                |
    +------------------+----------+------+-----+---------+----------------+
    5 rows in set (0.00 sec)

    mysql> show columns from doctypes;
    +-------------+-----------+------+-----+---------+----------------+
    | Field       | Type      | Null | Key | Default | Extra          |
    +-------------+-----------+------+-----+---------+----------------+
    | doctypeid   | int(11)   | NO   | PRI | NULL    | auto_increment |
    | title       | char(255) | NO   |     | NULL    |                |
    | description | text      | NO   |     | NULL    |                |
    | doctype     | char(255) | NO   | MUL | NULL    |                |
    +-------------+-----------+------+-----+---------+----------------+
    4 rows in set (0.00 sec)

    mysql>

Now, we probably want to do permissions differently in production, but for now it will be sufficiant and will make debug a bit easier.  (Note: we will touch on Database security and design changes after this first version is complete.)

###Database Access from Python###

Let's quickly look at how we would go about using the created tables.

    from models import *

    def geturls():
        urls = Urls()
        urllist = urls.getall()
        return urllist

    def printurls(urllist):
        for url in urls:
            # urlid,targeturl,maxlinklevel,creationdatetime,doctypeid = url
            print url
                
    def main():
        urllist = geturls()
        printurls(urllist)

    main()

The above code will import the models created by sql2api, and allow access to the Urls class which, in turn, allows access to the Urls table within the MySQL database.  The getall() function is built into each class generated by sql2api by default.  The printurls() function then just iterates through and prints all of the information from the row in the Database.  Note how each tuple in the array holds 5 items (the same 5 items that are in the table).

###Creating a New Database Accesser

Since it's impossible for the sql2api to know all of way queries we want to perform, as we come up with them we need to add Accessor.  Luckily sql2api places a nice little template at the end of each file it creates on how to add an Accessor, there for creating one is simple!

First, we need to define our query with the JOIN so we can get the information from both tables into a single response.

    SELECT
      urls.urlid as urlid,
      urls.targeturl as targeturl,
      urls.maxlinklevel as maxlinklevel,
      urls.creationdatetime as creationdatetime,
      doctypes.title as doctypetitle,
      doctypes.description as docdescription,
      doctypes.doctype as doctype
    FROM 
      urls 
    JOIN
      doctypes 
    ON
      urls.doctypeid = doctypes.doctypeid;

The above SQL select everything we are interested in across both the urls and the doctypes tables.  Next we need to place that into an Accesser function with our Urls class within Urls.py.

Let's look at our Accesser function:

    def getallurldata(self):
        try:
            con = self.__connect()
            with con:
                cur = con.cursor()
                cur.execute("""
                            SELECT
                              urls.urlid as urlid,
                              urls.targeturl as targeturl,
                              urls.maxlinklevel as maxlinklevel,
                              urls.creationdatetime as creationdatetime,
                              doctypes.title as doctypetitle,
                              doctypes.description as docdescription,
                              doctypes.doctype as doctype
                            FROM
                              urls
                            JOIN
                              doctypes
                            ON
                              urls.doctypeid = doctypes.doctypeid;
                            """)
                rows = cur.fetchall()
                cur.close()
            _urls = []
            for row in rows:
                _urls.append(row)
            con.close()
        except Exception, e:
            raise Exception("sql2api error - getall() failed with error:\n\n\t{0}".format(e))
        return _urls

We can see the large SQL query in the middle of the function.  The query is passed into the cursor within the connection to the MySQL database (note: we connect at the beginning of the function, and use the connection and cursor throughout the function).  At the end of the function we iterate through the response and place the data into a list of tuples.

Now we can call the getallurldata() function and get all of the meta data that we need to pass to the Scraper. 

###The Dispatcher###

Now that we have the Database defined, the Message Bus defined, and the Dispatcher payload defined we can put it all together into a single class:

    import pika
    import simplejson
    import uuid

    from models import *

    class Dispatcher():

        def __init__(self,address='localhost',exchange='barkingowl'):
            # create our uuid
            self.uid = uuid.uuid1()

            self.address = address
            self.exchange = exchange

            #setup message bus
            reqcon = pika.BlockingConnection(pika.ConnectionParameters(host=address))
            reqchan = reqcon.channel()
            reqchan.exchange_declare(exchange=exchange,type='fanout')
            result = reqchan.queue_declare(exclusive=True)
            queue_name = result.method.queue
            reqchan.queue_bind(exchange=exchange,queue=queue_name)
            reqchan.basic_consume(self.reqcallback,queue=queue_name,no_ack=True)

        def geturls(self):
            urls = Urls()
            allurls = urls.getallurldata()
            return allurls

        def start(self):
            self.urls = geturls()
            self.urlindex = len(self.urls)-1
            reqchan.start_consuming()

        def sendurl(self,url,destinationid):
            # unpack the tuple
            urlid,targeturl,maxlinklevel,creationdatetime,doctypetitle,docdescription,doctype = url
            isodatetime = strftime("%Y-%m-%d %H:%M:%S")
            packet = {
                'urlid': urlid,
                'targeturl': targeturl
                'maxlinklevel': maxlinklevel,
                'creationdatetime': creationdatetime,
                'doctypetitle': doctypetitle,
                'docdescription': docdecription,
                'doctype': doctype,
                'disparchdatetime': isodatetime,
            }
            payload = {
                'command': 'url_dispatch',
                'sourceid': self.uid,
                'destinationid': destinationid,
                'message': simplejson.dumps(packet)
            }
            jbody = simplejson.dumps(payload)
            respchan.basic_publish(exchange=exchange,routing_key='',body=jbody)

        # message handler
        def reqcallback(self,ch,method,properties,body):
            response = simplejson.loads(body)
            print "Processing Message:\n\n\t{0}".format(response)
            if response['command'] == 'scraperavailable':
                if len(self.urlindex) == -1:
                    self.urls = self.geturls()
                self.sendurl(self.urls[self.urlindex],response['sourceid'])
                print "URL dispatched to '{0}'".format(response['sourceid'])

    def main():
        print "BarkingOwl Dispatcher Starting."
        dispatcher = Dispatcher(address='localhost',exchange'barkingowl')
        dispatcher.start()
        print "BarkingOwl Dispatcher Exiting."

    main()

###What's Next?###

Next we need to polish up the Scraper, and write a simple Plugin to prove that everything is working!  Stay tuned for part IV in the BarkingOwl Design Series.
                                                             
      doctypes 
    ON
      urls.doctypeid = doctypes.doctypeid;

The above SQL select everything we are interested in across both the urls and the doctypes tables.  Next we need to place that into an Accesser function with our Urls class within Urls.py.



###What's Next###

Now that we have the Database defined, the Message Bus defined, and the Dispatcher payload defined we can put it all together into a single class: