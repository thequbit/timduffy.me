###The Order Of Things###

The next step part to define in the [BarkingOwl](https://github.com/thequbit/BarkingOwl) architecture is defining the Dispatcher.  This is the third part in the BarkingOwl Design Series ([one](http://timduffy.me/posts/barkingowl_architecture_design.html), [two](http://timduffy.me/posts/barkingowl_scraper_design.html)).

The Dispatcher is responsible for interfacing to a database of URLs to be scraped, and telling the Scrapers within the system to crawl them.  The Dispatcher communicates with the database via a direct link, and to the Scrapers via the Message Bus.

There needs to be a back-and-forth between the Dispatcher and the Scraper(s).  We need to define the order in which things need to happen in the system so we can better understand how the Dispatcher and the Scraper(s) will interact.

  1. **Launch the Dispatcher**
    - The Dispatcher needs to be the first part of the system to come online.  The Dispatcher will connect to the Message Bus and begin consuming messages (listening for messages on the Message Bus).
    - The Dispatcher listens on the Message Bus for Scrapers to announce themselves.

  2. **Launch the Scraper(s)**
    - The Scraper comes online and immediately announces it's state on the bus.  At this point the state will be 'idle', and thus is ready for a URL to be dispatched to it.
    - In the event that the Scraper doesn't get issued a URL, it will rebroadcast it's availability every 30 seconds.

  3. **Launch the Archiver**
    - More on it's task(s) later, but it only consumes - it does not broadcast any messages to the Message Bus.

  4. **Respond to Availability Broadcast**
    - The Scraper will broadcast an Availability Broadcast payload to the Message Bus.  The Dispatcher will consume this message, and response with a URL-To-Scrape payload.
      - Since every message is asynchronous and broadcast with no acknowledgement of receipt, the Dispatcher will keep track of how long a Scraper will expect Watch Dog ticks back from the Scraper.  More on this when we define the Dispatcher.

  5. **Begin Scraping**
    - The Scraper will consume the URL-To-Scrape payload that is issued to it (the Dispatcher will use the 'destinationid' field within the payload to direct the message to the correct Scraper.
    - The Scraper will look at the payload's 'message' field to pull out the URL and it's meta data.

  6. **Broadcast Found Documents**
    - Within the URL-To-Scrape payload is the URL to be scraped as well as the type of document to look for.  The Scraper will, every time it finds one of the document types it is supposed to be looking for, will broadcast a Document-Found payload to the bus.
    - Any client (Plugin) can consume the messages on the Message Bus.  What the consumer does witht he data, is up to it and is not defined within the BarkingOwl system.

  7.  **Broadcast Scraper Success**
    - Once the Scraper is done with scraping the URL it has been assigned, it needs to tell the Dispatcher as well as the Archiver.
       - This is the first time we are really working with the Archiver.  Since it is not very well defined yet, let's just say that it is the keeper of the Scraper(s) status (such as when the Scraper has run, what URL it scraped, its successes and failures, etc.).

  8. **Rinse and Repeat**
    - Once the Scraper has completed scraping the URL it was dispatched, it broadcasts it's availability on the bus and waits for the Dispatcher to send another URL-To-Scrape payload to it to start on.

###The Dispatcher###

The Dispatcher acts as the interface between the Database that holds the URLs (and their Meta Data) and the Scrapers that will scrape them.

The Dispatcher needs to fulfill these tasks:

  1. Pull URLs and URL meta data from the Database
    - This can be done each time a request comes in, or based on a time period (ie. every 24 hours).
    - I will be using another tool I wrote called [sql2api](https://github.com/thequbit/sql2api) to interface between Python and the Database.

  2. Dispatch URL-To-Scrape payloads to Scrapers
    - The Dispatcher will take the URL and it's meta data and serialize it to the 'message' part of the payload.

  3. Record the last time a URL has been scraped
    - I believe it is important to keep track of the Scraper(s) successes and failures, however this data will be kept within the Archivers database.  I am going to keep this requirement in for now, but I don't think it will be implemented in the first go-around. 

I have thought that it would be nice to have one of the things that the Dispatcher handles is how often the URL is scraped.  Now, this could be a global value set for the entire system, or it could be set per-URL.  For now, I believe setting the value globally shall be sufficient - but i can see where that could be a waist of bandwidth in certain applications.

The Database for the Dispatcher will be MySQL based.  The database will be loaded by a separate entity other than the Dispatcher (such as a small web framework allowing for a simple HTTP JSON API).

###The Archiver###

The Archiver is responsible for consuming all messages on the bus and keeping track of them.  A great way to think of the Archiver is simply a system-wide log file.  Due to the variability of the 'message' portion of a message payload, we will be using a NoSQL database to save the contents to, in this case MongoDB.

This is, for those who have read the previous posts in this series, different then the original architecture I defined in post [one](http://timduffy.me/posts/barkingowl_architecture_design.html).  A big part of this design series is backing up and checking the design decisions that I made when starting the project.  In this particular case, it makes a lot more sense to use the flexibility of data types and values within a MongoDB rather than be forced into the rigidity of an SQL database.

The other thing you will notice is that the Archiver and the Dispatcher no longer share the same database.  This divorce was intentional, as the Dispatcher's requirements for the Database is much different than that of the Archiver.

The Archiver will simply consume all messages on the Message Bus and push them to the MongoDB for latter consumption.  If there is a desire to view/review/mine the data within the MongoDB database, then a separate connection/interface must be used.

**Note:** The system does not require the use of the Archiver, it simply is a diagnostic and debug tool.

###What's Next###

Next step is to start putting it all together!  The next post, hopefully, will be a status update on my successes and failures in implementing the system that I have defined.  I believe I have just about all of the parts I need to implement a first revision of the base system with no Plugins.