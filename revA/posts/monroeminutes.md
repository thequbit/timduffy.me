##Monroe Minutes##

In August of 2011 I came up with an idea that I called 'Monroe Minutes'.  I wanted to scrape all of the towns, villages, cities websites' within Monroe County, NY and pull down all of their meeting minutes to make them searchable from a single portal.  It was a rather ambitious project, but I thought it was a meaningful one.

If you check the commit logs on the github [repo](https://github.com/thequbit/monroeminutes) you can see that the first commit was on December 3rd, 2012.  This was the date of one of my very first hackathons, Random Hacks of Kindness.  This event was run locally by Remy DeCausemaker, and went off without a hitch!  You can learn more about RHoK [here](http://rhok.org) and [here](http://en.wikipedia.org/wiki/Random_Hacks_of_Kindness).

I have written about Monroe Minutes before in a few posts, specificly the Barking Owl Series ([Part I](http://timduffy.me/posts/barkingowl_architecture_design.html), [Part II](http://timduffy.me/posts/barkingowl_scraper_design.html), [Part III](http://timduffy.me/posts/barkingowl_the_order_of_things.html), [Part IV](http://timduffy.me/posts/barkingowl_dispatcher_design.html), [Part V](http://timduffy.me/posts/barkingowl_working_code.html)).  [BarkingOwl](https://github.com/thequbit/BarkingOwl) was a venture into a reusable tool that would assist me in writing powerful web scrapers.  My first attempt to use BarkingOwl as the underlying technology in a project is with Monroe Minutes.

###What is Monroe Minutes###

My goal for Monroe Minutes was to create a portal for anyone to search for keywords and phrases within all meeting minutes from the various groups, organizations, and government agencies within Monroe County, NY.

It is always a goal to create things that are reusable, however sometimes that requirement drives more of your development time than the actual thing you are trying to create.  When this happens its important to step back, and make sure what you are spending your time on is really worth your while.

With Monroe Minutes, my first attempt was a very naive attempt at a web scraper that needed to be pointed to a specific page to pull PDF documents off of.  Not a terrible start, but very labor intensive to setup, since every single page on all town websites that contained PDF documents needed to be found.  The other short fall of this attempt was using [nltk](http://nltk.org/) (Natural Language Tool Kit) to generate a histogram of words, and then use that list of words to perform the search.  Although it did produce results, ranking was nearly impossible.

After almost half a year of fiddling with code here and there (feel free to check the commit logs on the repo, you can see I go hot and cold pretty regularly), I was re-inspired by a journalist out of the more southern part of the state (Binghamton south, not NYC south).  He wanted to look for keywords in real-time within meeting minutes.  He had communicated his need(s) well, and was super passionate about how helpful it would be.

I was re-energized, I was going to break out some of the important parts of Monroe Minutes, and try and apply them to the problem.

###PDFImp###

The next big step in the evaluation of Monroe Minutes, was a tool I called [PDFImp](https://github.com/thequbit/pdfimp).  PDFImp was the third generation of web scraper that was the heart of the Monroe Minutes scraper.  The tool would be a stand-alone scraper that would be pointed at a URL, and return a list of all PDF documents that it found.

There were some issues with the method I chose:

  - The tool did not return the PDF list until it was complete.
  - It held all of the information for the PDF (including all of its text) in memory
    - This means that with a site that was hundreds of PDFs, you could be eating up GB of memory.
  - The scraper wasn't very smart, it would look at the same page multiple times

Not a bad start.  In initial tests, the tool worked well.  It really thrashed the site that it was looking at since it wasn't smart enough not to look at the same page more than once, but over all not too bad.  The biggest part of PDFImp that I didn't like was the fact that it didn't spit anything out until it had scraped the ENTIRE site.  In one test it visisted 50,000 links, however there were only 40 or so pages on the entire site ...

###Barking Owl - revA###

Barking Owl started as the 'answer' to implement the solution to the 'meeting minutes phrase detection' problem presented to me earlier in the summer of 2013.  I was going to call PDFImp with information from a database, and put a web front-end on it.  I was ready to push out a site within a weekend!

Aaaaand then I got into the code.  I realized that there was just so many sites to scrape, I was going to need a much more scalable solution than a single-threaded python script.  I realized I needed a way to spin up threads to do both scraping and PDF processing.  This was the first time I got around to looking at lots of sites at the same time, and what I saw was the PDF->Text processor hammering on the processor and pausing the script for, sometimes, minutes.

The first commit to the BarkingOwl repo is August 6th, 2013.  There is a branch called 
'working_revA' that essentially pulling urls from a database and pushing them to PDFImp.  Not the most elegant solution, but it *does* work.

###Barking Owl - revB###

The next version of BarkingOwl was a complete redesign, and was a culmination of lots of learning experience.  You can read all about how it works in the 5 part design series i linked above.

What I have added to BarkingOwl is the ability to call it as a library and extent its functionality, rather than just interact with it via the RabbitMQ bus.  This has been incredibly successful in using it to implement Monroe Minutes, as it prevented a lot of code being written, as well as reduced overhead on the system that can be used for PDF conversion and URL scraping.

The current version of BarkingOwl uses all of the topics mentioned in the BarkingOwl Design Series, and is currently working much better than I expected :p

###The Design###

The design of Monroe Minutes is very similar to BarkingOwl with a few small additions:

![Monroe Minutes Design][1]

The introduction of ElasticSearch allows for robust, fast indexing, and solves the issue that using the nltk histograms could not in the previous version(s).

###Monroe Minutes - The Parts###

There are a few parts to Monroe Minutes

  - **monroeminutes_dispatcher.py**
    - This extends the barkingowl_dispatcher.py script.
    - This script pulls URLs from the database, and serves them up to the RabbitMQ bus as scrapers become available.

  - **monroeminutes_scraper.py**
    - This extends the barkingowl_scraper.py script.
    - This script listens for a URL to be sent to it via the RabbitMQ bus.  It then scrapes that URL and broadcasts and PDF documents it finds to the RabbitMQ bus.

  - **monroeminutes_archiver.py**
    - This uses the same method of interfacing to the RabbitMQ bus as the diagoutput example from BarkingOwl.
    - This script listens on the RabbitMQ bus for new PDF documents.  Once seen, it converts them to text, and pushes their meta data to the database and their full text to [ElasticSearch](http://www.elasticsearch.org/) to be indexed.

  - **monroeminutes_shutdown.py**
    - This uses the GlobalShutdown class within BarkingOwl to shutdown the entire MonroeMinutes system.
      - Note: at the time of this blog post, the scraper needs to complete scraping before exiting.  Not entirely sure why this is happening at the moment - it's logged as an issue in BarkingOwl.

  - **monroeminutes_web.py**
    - This script provides a web interface to the ElasticSearch index and various meta data within the database.

###What's Next?###

The next step will be to fully design the database as well as defined what is passed to ElasticSearch.

The database needs to hold enough information about the county and it's various bodies and organizations.  It needs to be determined still how the data should be split between elastic search and the sql database.

 

  [1]: http://timduffy.me/posts/media/monroeminutesarch.png