##MonroeMinute System Overview##

On Friday the 21st of February I had the pleasure of spending several hours at the RIT MAGIC center for the AT&T Rochester Civic Apps Challenge.  The event was sponsored by AT&T, Digital Rochester, High Tech Rochester, and Hack Upstate.  I decided that I would submit MonroeMinutes to the 'existing applications' category.  Below is a full system overview of the different parts of the MonroeMinutes system.

##Parts##

***Database***

  The database within the MonroeMinutes system is [MongoDB](http://www.mongodb.org/).  The MongoDB database is a NoSQL database that holds information about the entities within Monroe County (Towns, Villages, and Cities), Organizations within those entities (A Town Board or Zoning Board), Documents (found PDF, their text, and meta data), as well as some information about the system health and users.  Here are the schemes for each collection within the database:

The entities collection holds information about each Town, Village, and City within Monroe County.  Here is an example entry:

    entity = {
        "_id": "530c00586c5bc4160b2e9132",
        "website": "http://www.townofbrighton.org/",
        "name": "Town of Brighton",
        "description": "Brighton, NY"
        "creationdatetime": "2014-02-24 21:30:48",
        "orgs": [
            "53085f0ea70f9e0e63aeb15a",
            "507f191e810c19729de860ea",
            "507f1f77bcf86cd799439011",
        ]
    }

The organizations collection holds information about each of the organizations within an entity.  Note that an org does not know what entity it belongs to.  Also note that all strings within the matchtext array much exist within the document to successfully match.

    org = {
        "_id": "53085f0ea70f9e0e63aeb15a",
        "name": 'Town Board",
        "description": "Brighton Town Board",
        "matchtext": [
            "MINUTES OF TOWN BOARD MEETING",
            "TOWN OF BRIGHTON"
        ]
    }

The largest collection within the database is the documents collection.  This collection holds information about each found pdf document including it's full converted text.  Some things to note:

  - The urldata is exactly what was passed to the scraper from the dispatcher (see dispatcher section below).

  - Adobe, in all of their infinite wisdom, allowed the 'created' field within the PDF format to be free-form text, thus resulting in no defined format for the time/date of creation.  This field should not be used to determine ... anything.

  - the pdfhash field is the MD5 hash of the pdftext field.

  - the orgid and entityid are the ObjectId() within the MongoDB database of the entity and organization that the document belongs to.  Both are saved for simpler searching.

A document looks like this:

    doc = {
        "_id": "530c00d16c5bc416257b4d3f",
        "scrapedatetime": "2014-02-24 21:32:28",
        "minutesdate": "",
        "created": "",
        "being_converted": false,
        "converted": false,
        "being_processed": false,
        "processed": false
        "filename": "Historic-Consultant.pdf",
        "docurl": "http://www.brockportny.org/pdf/historic-preservation/Historic-Consultant.pdf",
        "linktext": "View the Press Release",
        "docname": "/mnt/sas/monroeminutes/downloads//Historic-Consultant.pdf_1393295569.1.download",
        "pdftext": "",
        "pdfhash": "",
        "entityid": "530c00586c5bc4160b2e9133",
        "orgid": "",
        "urldata": {
            "status": "running",
            "maxlinklevel": 4,
            "runs": [
                
            ],
            "description": "Brockport, NY",
            "title": "Village of Brockport",
            "scraperid": "ca7e00d7-f870-455a-8c60-98722e4f1a8d",
            "doctype": "application/pdf",
            "frequency": 10080,
            "startdatetime": "2014-02-24 21:32:24",
            "targeturl": "http://www.brockportny.org/",
            "finishdatetime": "",
            "entityid": "530c00586c5bc4160b2e9133",
            "creationdatetime": "2014-02-24 21:31:10"
        }
    }

Finally we save all of the scraper runs in the database.  This is used more for monitoring and administration/debug purposes.  We will be able to, however, generate some very cool statistics from this data.

    run = {
        "_id": "530c366c6c5bc416257b684e",
        "bandwidth": 194555,
        "startdatetime": "2014-02-24 22:41:26",
        "linkcount": 1624
        "urldata": {
            "status": "running",
            "maxlinklevel": 4,
            "runs": [
            
            ],
            "description": "Webster, NY",
            "title": "Village of Webster",
            "scraperid": "30c0775d-fd8e-48b8-ae79-ca487251cbcc",
            "doctype": "application/pdf",
            "frequency": 10080,
            "startdatetime": "2014-02-24 22:40:48",
            "targeturl": "http://www.villageofwebster.com/",
            "finishdatetime": "",
            "entityid": "530c00586c5bc4160b2e914b",
            "creationdatetime": "2014-02-24 21:31:10"
        },
        "badlinks": [
            "mailto:amchampagne@villageofwebster.com"
        ],
        "processed": [
        
            ... links processed here ...
        
        ],
        
    } 

Now that we have outlined the database design, and what it holds, we can move onto how each part of the system creates and uses that data.

***Dispatcher***

  The dispatcher is responsible