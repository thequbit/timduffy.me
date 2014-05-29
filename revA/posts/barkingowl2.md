If you've been following along with the progression of [BarkingOwl](https://github.com/thequbit/BarkingOwl) in one of my previous [posts](http://timduffy.me/posts/barkingowl_architecture_design.html), you will be excited to know this the next post in the series.

I identified a number of different parts of the system in my last post, but let's review them quickly:

 - **Message Bus**
  - The means for all parts of the system to communicate
 - **Dispatcher**
  - Responds to Scraper requests for work with a URL and URL meta data
 - **Archiver**
  - Is responsible for keeping track of work being done by the Scraper(s)
 - **Scraper**
  - Crawls websites looking for specific document types
 - **Plugin(s)**
  - Consumes messages from the Message Bus and processes them as it deems fit

This post will primarily focus on the Scraper portion of the above system, as it took quite a bit of time to get it to do what I wanted it to do.  Interestingly enough many of the local government websites I came across in my testing were not very well written ... My particular favorite are links that go above the root of the site.  An example of this would be a link on the index.html page sitting in the root of the domain that looks like this:

    <a href="../../pdfs/notes_11_14_2013.pdf">November 14th Meeting Minutes</a>

This, of course, does not resolve to anything because you can't go higher than the root within the 'file system' of the website.  One thing that I did find interested was that Chrome, Firefox, and IE all resolve this just fine.  They much be just removing the '../' and taking it as './pdfs'.

Anyway, the point is the Scraper ended up needing more intelligence then I originally thought it would, and it still has a long way to go.

###The Scraper Packet Definition###

The next big step is getting the Scraper to a point where it can be dispatched a URL and some meta data and crawl a website.  First, we need to defined what the message packet of the payload is going to look like:

     # capture the iso date/time
     isodatetime = strftime("%Y-%m-%d %H:%M:%S")

     # create packet
     packet = {
         'crawlurl': crawlurl,
         'crawlurltitle': crawlurltitle
         'docurl': docurl,
         'doctype': doctype,
         'linktext': linktext,
         'currentlinklevel': linklevel,
         'scrapedatetime': isodatetime,
     }

     # create Scraper Payload
     payload = {
         'command': 'found_doc',
         'sourceid': '',
         'destinationid': 'broadcast',
         'message': simplejson.dumps(packet)
     } 

     # send Scraper Payload
     jbody = simplejson.dumps(payload)
     respchan.basic_publish(exchange=exchange,routing_key='',body=jbody)

Now there are some unknowns in the above, let's go through the above code step by step.


  - **crawlurl**
    - The crawlurl is the URL that was dispatched by the Dispatcher to the Scraper when the Scraper announced that it was running and not currently busy.  This will be something like 'http://www.henrietta.org/'.

  - **crawlurltitle**
    - This will come with the URL from the dispatcher as part of the meta data that is included in the Dispatchers response packet to the Scraper.  This can be used as a nice human readable method of displaying data within the plugin

  - **docurl**
    - This is the URL of the document that the Scraper found.  This will look something like 'http://www.henrietta.org/index.php?option=com_docman&task=doc_download&gid=2066&Itemid=240' - not the prietiest thing, but that is where a document is kept.

  - **doctype**
    - this is the type of document that the magic library (yes it is actually called magic) determined the document was.  An example could be 'application/pdf'.  Note that the Scraper is downloading the first small bit of the file to undermine what kind of file it is.  The other method would be to look at the server response header and look at the type - I found this to be unreliable.

  - **linktext**
   - This is the text between the a tag that was the link.  This can be useful later to determine additional data about the file.

  - **currentlinklevel**
    - This is the current number of links that the Scraper had to follow to get to this point.  This can be useful for diagnosing Scrapers that run for a very long time.  If all of the documents are found at the maximum allowed level, then it might be wise to make the crawlurl lower down the site file system.

  - **scraperdatetime**
    - This is simply the data and time that the Scraper found the file.  It is saved in standardized ISO format. (note: you can not serialize the datatime object into a pika message payload, so that is why I store it this way).

Now that we have the packet that the Scraper will be blasting out on the Message Bus defined, we can go ahead and put together the actual Scraper :p.

###Core Scraper Code###

I wrote a small utility in the beginning of the BarkingOwl project that was based off of the work I had done with Monroe Minutes.  I called it [pdfimp](https://github.com/thequbit/pdfimp).  It effectively would crawl a URL and spit back all of the PDF files it found.  It was my 'first attempt' at the underbelly of BarkingOwl.  I thought it was useful enough by itself I split it out and made it it's own utility.

After a few tweaks and revisions, I came up with the following code snippet:
  
    # our globals
    _level = -1
    _processed = []
    _badlinks = []

    # list of documents we want to look for
    doctypes = ['application/pdf',]

    def followlinks(orgid,urlid,maxlevel,siteurl,links,level=0,filesize=1024):
        retlinks = []
        _level = level
        if( level >= maxlevel ):
            pass
        else:
            level += 1
            for _link in links:
                link,linktext = _link
                
                # we need to keep track of what links we have visited at each 
                # level.  Here we are adding to our array each time a new level 
                # is seen
                if len(self._processed)-1 < level:
                    _processed.append([])

                # see if we have already processed the link at max level, and we
                # are at maxlevel.  If that is the case, it is pointless to do the 
                # bottom of the tree over and over again.  Also don't do anything 
                # if it is 404/bad link
                if (link in _processed[level-1]) or link in _badlinks:
                    continue

                # get all of the links from the page
                ignored = 0
                allpagelinks,success = getpagelinks(siteurl,link)
                if success == False:
                    continue
                
                # sanitize the url link, and save it to our list of processed links
                _l = urljoin(siteurl,link)
                _processed[level-1].append(_l)
                
                # Look at the links found on the page, and add those that are within
                # the domain to 'thelinks'
                pagelinks = []
                for pagelink in allpagelinks:
                    match,link,linktext = pagelink
                    if( match == True ):
                        pagelinks.append((link,linktext))

                # Some of the links that were returned from this page might be pdfs,
                # if they are, add them to the list of pdfs to be returned 'retlinks'
                for _thelink in pagelinks:
                   thelink,linktext = _thelink
                   if not any(thelink in r for r in retlinks):
                        success,linktype = typelink(thelink,filesize)
                        if success == True and linktype in doctypes:
                            retlinks.append((thelink,linktext))
                            _processed[level-1].append(thelink)
                            
                            # TODO: broadcast message here!

                        else:
                            ignored += 1

                # Follow all of the link within the 'thelink' array
                gotlinks = followlinks(orgid=orgid,
                                       urlid=urlid,
                                       maxlevel=maxlevel,
                                       siteurl=siteurl,
                                       links=pagelinks,
                                       level=level,
                                       filesize=filesize,
                                      )
                
                # go through all of the returned links and see if any of them are docs
                for _gotlink in gotlinks:
                    gotlink,linktext = _gotlink
                    if not any(gotlink in r for r in retlinks):
                        success,linktype = typelink(gotlink,filesize)
                        if success == True and linktype in doctypes: 
                            retlinks.append((gotlink,linktext))
                            _processed[level-1].append(gotlink)

                            # TODO: broadcast message here!

                        else:
                            ignored += 1
            level -= 1
        for l in links:
            if not l in _processed:
                _processed.append(l)
        return retlinks

Okay, I know ... that's kind of a lot of code to just throw at you - but it's not that bad, I promise!  Let's take a look and see if we can decode everything.

First, one of the things that we need to do is minimize [DOS attacks](http://en.wikipedia.org/wiki/Denial-of-service_attack) on a town website.  We can do this by not thrashing the site any more than we need to by keeping track of what pages we have pulled down at what level.  Let me take a moment to say that this is my first hardcore dive into web scraping, and I am sure the Scraper is not perfect.  This is just simply my take on a 'pretty good' method for not downloading a single file too many times.  I hope to make lots of revisions to the Scraper over time to make it more efficient and less load on the target website(s).

What this function is designed to do, is speaking in high level terms, is to:

 1. Be presented with a URL
 2. Look at every link on that page and see if any of them are of the type of doc we are looking for
 3. Follow every link on that page recursively until a 'maximum level' of links is found performing the same function as item 2.
 4. Do not look at a file more than once per level.  That is, if index.html is looked at on level 1, don't look at it again on level 2 since the links will not be able to be followed as deeply.

This will result in the crawler viewing the entire site, restricted by link level, and find all of the docs on the site.

You will notice that there are a few functions that I call that are not defined in the above code.

  - **getpagelinks()**
    - This uses a very awesome library called [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/) to navigate the DOM of the page and pull out all of the links.

  - **typelink()**
    - This function uses the magic library to determine the type of the file.  It downloads the first 2K of the file and passes it to magic and, if successful, returns the file type.

  - **followlinks()**
    - The function calls itself to continue to follow the file system tree in a recursive manor.  I am sure this could be threaded to become very fast - but for right now this should be fine.

The last slightly confusing part about the above code is the two for loops that iterate through the current page links, and all returned page links from the recursive call to followlinks().  Both of these are actually doing the same thing: looking at the links and trying to find out if the link is of the type of doc we are looking for.  They also keep track of what links they have processed already as to not thrash the target URL.

For your enjoyment, here is the getpagelinks() function:

    from urllib2
    from bs4 import BeautifulSoup
    from urlparse import urljoin

    def checkmatch(siteurl,link):
        sitematch = True
        if ( (len(link) >= 7 and link[0:7].lower() == "http://") or
             (len(link) >= 8 and link[0:8].lower() == "https://") or
             (len(link) >= 3 and link[0:6].lower() == "ftp://") ): 
            if(link[:link.find("/",7)+1] != siteurl):
                sitematch = False
        return sitematch

    def getpagelinks(siteurl,url):
        links = []
        success,linktype = typelink(url,2048)
        if success == False:
            badlinks.append(url)
            return links,success
        sucess = True
        if linktype != "text/html":
            return links,False
        try:
            html = urllib2.urlopen(url)
            soup = BeautifulSoup(html)
            atags = soup.find_all('a', href=True)
            for tag in atags:
                if len(tag.contents) >= 1:
                    linktext = unicode(tag.string).strip()
                else:
                    linktext = ""
                rawhref = tag['href']
                match = checkmatch(siteurl,rawhref)
                abslink = urljoin(siteurl,rawhref)
                links.append((match,abslink,linktext))
                # there are some websites that have absolute links that go above
                # the root ... why this is I have no idea, but this is how i'm
                # solving it
                uprelparts = rawhref.split('../')
                if len(uprelparts) == 1:
                    abslink = urljoin(siteurl,rawhref)
                    links.append((match,abslink,linktext))
                elif len(uprelparts) == 2:
                    abslink = urljoin(siteurl,uprelparts[1])
                    links.append((match,abslink,linktext))
                elif len(uprelparts) == 3:
                    newhref = "../{0}".format(uprelparts[2])
                    abslink = urljoin(siteurl,newhref)
                    links.append((match,abslink,linktext))
                    abslink = urljoin(siteurl,uprelparts[2])
                else:
                    abslink = urljoin(siteurl,rawhref)
        except Exception, e:
            links = []
            sucess = False
            
        self._linkcount += len(links)
        return links,True

And here is the typelink() function:

    import urllib2
    import magic

    def typelink(link,filesize):
        req = urllib2.Request(link, headers={'Range':"byte=0-{0}".format(filesize)})
        success = True
        filetype = ""
        try:
            payload = urllib2.urlopen(req,timeout=5).read(filesize)
            filetype = magic.from_buffer(payload,mime=True)
        except Exception, e:
            success = False;
        return success,filetype

Using those four functions: followlinks(), getpagelinks(), checkmatch(), and typelink() the Scraper is almost complete.  We just need to wrap it with some intelligence logic and Message Bus communications support.

###The Scraper Wrapper###

