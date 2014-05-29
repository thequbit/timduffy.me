###Monroe Minutes Database Design###

The Monroe Minutes system is built using BarkingOwl.  The BarkingOwl subsystem is simply fed data, it does not directly interface with any kind of database.  Therefore, part of the MonroeMinutes wrapper around BarkingOwl needs to have some kind of data container within it - in this case it will be a MySQL database.

The organization that I have picked is one of two tiers: *bodies* and *organizations*.  Bodies are entities such as towns, villages, hamlets, and cities.  Organizations are groups such as Town Boards, Zoning Boards, and Planning Boards.  A *body* can hold multiple *organizations* in this configuration.

Let's look at some SQL:

    CREATE TABLE IF NOT EXIST bodies(
        bodyid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        name CHAR(255) NOT NULL,
        description TEXT NOT NULL,
        creationdatatime DATETIME NOT NULL
    );
    CREATE INDEX bodies_bodyid ON bodies(bodyid);

Since a *body* is the high level in the tree, it does not reference anything.

Let's look at the SQL for an organization:

    CREATE TABLE IF NOT EXISTS orgs(
        orgid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        name CHAR(255) NOT NULL,
        description TEXT NOT NULL,
        creationdatetime DATETIME NOT NULL,
        matchtext TEXT NOT NULL,
        urlid INT NOT NULL,
        FOREIGN KEY (urlid) REFERENCES url(urlid),
        bodyid INT NOT NULL,
        FOREIGN KEY (bodyid) REFERENCES bodies(bodyid)
    );
    CREATE INDEX orgs_orgid ON orgs(orgid);

Since an *organization* "belongs" to a *body*, it references it within the database.

There is a column within the orgs database called 'matchtext'.  The matchtext is a phrase that should be used to determine what organization within a body a document belongs to.  There are, of course, some issues with this particular method of matching, however I believe it is an appropriate one based on the use cases.

One of my biggest hopes for Monroe Minutes is that it is used by citizens all over Monroe County and New York State to become more informed about what is going on in their town and county, and thus make more informed decisions when voting (as well as other things).  My second biggest hopes for Monroe Minutes is for the tool to be used by others all over the US and the world to do the same for their communities.

Since not everyone will be a regex and sql master, the goal is for anyone to type in a string that could be matched and to have the tool do the 'magic' behind the scene.  My goal is to have this text be something such as "Planning Board" or "Town Board" or "Town of Scottsville".  This text, with some serious regex power, will be used to match to the first "section" of the PDf.  I would assume this would be the first 4096, or 8192 characters of the document, but this will take some experimentation to get perfect.

Note that there also is a reference to a urlid within the orgs table.  The other part of the database is the list of URLs.  Since multiple organizations could reference the same URL (think the town board, the planning board, and the zoning board of Henrietta will all point to http://henrietta.org/), we will have multiple organizations referencing the same urlid within the urls table.

The SQL:

    CREATE TABLE IF NOT EXISTS urls(
        urlid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        targeturl TEXT NOT NULL,
        title CHAR(255) NOT NULL,
        description TEXT NOT NULL,
        maxlinklevel INT NOT NULL,
        creationdatetime DATETIME NOT NULL,
        doctype CHAR(127) NOT NULL,
        frequency INT NOT NULL
    );
    CREATE INDEX urls_urlid ON urls(urlid);

The table holds a small amount of information, but gives the monroeminutes_dispatcher.py script and BarkingOwl library everything that it needs to pull pdf documents out of the URL.  Let's take a look at some of its parts:

  - targeturl
    - This is the URL that the BarkingOwl scraper(s) will scrape.
    - example: http://scottsville.org/

  - title
    - A meaningful title to be displayed

  - description
    - Any additional information that may be useful to attach to the URL

  - maxlinklevel
    - This is the maximum number of links that the BarkingOwl scraper will follow.  This is very important to get 'correct'.  The larger this number the longer the scraper will run, the longer it will take to get all of the PDF documents out of the URL, and the most bandwidth the scraper will take.  A level larger than 3 is **strongly** discouraged.

  - doctype
    - This is a very important field as it is a string that is directly compared within BarkingOwl.  This is the document type returned by the [magic library](http://linux.die.net/man/3/libmagic) in Linux.  For PDF documents it is 'application/pdf'.  For HTML it is 'text/html'.

  - frequency
    - This is a number, in **minutes**, that tells the monroeminutes_dispatcher.py script how often it should dispatch the URL to the waiting scrapers.

###ElasticSearch###

The other storage part of Monroe Minutes is [ElasticSearch](http://www.elasticsearch.org/).  I had originally thought that I would keep a list of all of the documents that were found within both the database and ElasticSearch, however that seems both unnecessarily redundant and dangerous.

So, at least for now, I have decided for the contents in the MySQL database to be a single direction into the system, and document data one direction out of the system to ElasticSearch.  With each URL will then need to be sent all of the meta data for all organizations that is associated with it.  This does produce some additional overhead, however I think it is an elegant solution.

###Flow###

The flow of data looks like this:

![Monroe Minutes Flow][1]

Data about *bodies*, *organizations*, and *urls* is loaded into the MySQL database, then passed into the BarkingOwl subsystem, then finally (after being processed) is passed into ElasticSearch to be indexed.

###What's Next?###

I need to rework how I was thinking of the data flow, as I was having the Archiver write data back to the database.  I also need to figure out what to do with docs that are not assigned to an organization (I think marking them as 'misfit' is appreciate for now).  I also need to work on the administration pages for the website.  And, finally, figure out how to search by organization and not within the entire ElasticSearch index.


[1]: http://timduffy.me/posts/media/monroeminutesflow.png
