I have posted previously about a project I started back in August of 2013 called [BarkingOwl](https://github.com/thequbit/BarkingOwl).

It has, since then, been in the back of my mind to the best way to implement this rather large undertaking.  Perhaps a small amount of explaining of what I am trying to do with make the scope easier to understand.

Back in July of 2013 Innovation Trail put on a 'friendraiser' in Syracuse which I and other Hacks/Hackers Rochester people attended.  After the event we went to a local watering hole and began to discuss the landscape of jurnalism and swap war stories.  I had the privilege of speaking to a journalist on the Innovation Trail team that had a particular need:

> " I need to get real-time notifications based on phrases being used within meeting minutes across dozens of towns. "

I was immediately intrigued, as this played right into the work that I had been doing with [Monroe Minutes](https://github.com/thequbit/monroeminutes).  Specifically, one of the things I was not very happy with decisions that were made about Monroe Minutes was the fact that it required so much 'human intervention' to setup, thus making is very difficult to deploy in other counties.  I took this particular 'request' as a great opportunity to rethink what I was doing with Monroe Minutes, and create a more 'generic' tool.

###The Requirements###

First, I needed to come up with an architecture that would allow me to do what I wanted.  I came up with a few basic requirements:

 1. The architecture must be scalable 
  - I really don't like the term 'scalable' for a number of reasons: 1) *how* scalable, and 2) do you *really* need it to scale?
  - My goal was to allow multiple scrapers to run at once, so more could be accomplished in the same amount of time.  "Hardware is cheap" is something we hear a lot.

 2. The system must support plugins to allow for data capture and manipulation
  - My goal here was to allow for the tool to find documents on a website, and then send some kind of notification that the document was found, nothing more.  Then plugins could be written to allow anyone to do anything they wanted with those documents.

 3. It must be easy to use
  - this is tough, because what is easy to use for me might be rather difficult for something else.  I wanted it to be a 'it just works' kind of easy.  This will require a lot of documentation to accomplish I would think ;p

###The Architecture###

I imagined the tool to be one of three parts:

 1. The Dispatcher
  - The Dispatcher is responsible for giving work to the Scrapers
     - Think of this as a queue of all possible work (list of URLs to process).

 2. The Scraper
  - The scraper is really the heart of the tool.  It will go out and scrape the website, finding all documents (of any kind) and broadcast those documents to the message bus.
  - Anything that is subscribed to the message bus will then be able to work with that data.
  - To be 'scalable' the system much allow for n scrapers (note at some point the bus will just become so congested that it won't make sense to run any more scrapers.  We can slay that dragon when we get to it).

 3. The Archiver 
  - The Archiver will keep track of the work that the Scrapers have done.
      - This will hold all pages the scraper sees, and of what type they are.

 3. Plugins
  - This is where the tool really gets powerful.  Any piece of code can be written to listen to the bus and process the data that the scrapers are finding.
  - These tools can be written in any language, and can sit on any kind of hardware within the network that the message bus is broadcasting to.
     - A great example of a plugin would be a PDF->TXT decoder.  This would be the case for our phrase detector and Monroe Minutes use cases.

###The Message Bus###

One of the important choices to make is the Message Bus technology.  The technology used will dictate how easy Plugins are to write, also a number of other not immediately well understood things such as message congestion.

There are a number of options here, all with positives and negatives.  I have chosen, right or wrong, to go with [0mq](http://zeromq.org/), specifically [RabbitMQ](http://www.rabbitmq.com/).  0mq is a pretty slick message bus system that is based on a central hub, that is that there is a service running that all messages pass through before they are dispatched to listeners.

I am a bit concerned about possible congestion when dealing with lots of messages from dozens (hundreds!?) of Scrapers, but I don't think it will be too bad.  Nothing we can do but try it out!

Note: I came across this [blog post](https://blogs.vmware.com/vfabric/2013/04/how-fast-is-a-rabbit-basic-rabbitmq-performance-benchmarks.html) on vmwares website that sounded pretty promising - so let's do it!

###Application Flow###

The goal would be to have a Scraper come online and broadcast it's availability.  The Dispatcher would then send it a message with a URL payload (that would include the URL and any needed meta data such as what kind of documents to search for).  The Scraper would then scrape the URL finding any number of different document types (HTML, PDF, MS Doc, MS XLS, ODT, etc.) and broadcast out to the bus any document URL that match the pattern.  The document URLs would then be saved off to the database using the Archiver (Note: I think the Archiver is important in this architecture, however its exact use is not yet clear).  Lastly, any plugin listening to the Message Bus and looking for messages specific to a URL or a document type will be able to process that document appropriately (such as download a PDF and convert it to Text).

    picture of arch here!

Above is the *rough* idea of what I am thinking for the flow of things.  The visualization was done using Google Drive.

###Communications Layer###

First, I needed to install and configure RabbitMQ.  I will be running Ubuntu 12.04 LTS for this project, and there is an existing RabbitMQ package maintained for it.  I used this [link](http://www.rabbitmq.com/install-debian.html) as a reference.

To install the broker:

    # apt-get install rabbitmq-server

To start the broker:

    # service rabbitmq-service start

Nice and easy!  I am confident that there will be more configuration later on for performance, but for the moment this will do.

Next let's take a look at what our options are for python communicating with the RabbitMQ broker.  The package that I chose was [pika](https://pika.readthedocs.org/en/0.9.13/).  I had actually tried a few, but this seemed to make the most sense to me, and it came with, in my opinion at least, great documentation and example code.

To install pika:

    # pip install pika

**Consuming Messages**

Now let's look at the code!  There are two parts to the message bus 1) sending messages, and 2) consuming messages.  First let's look at consuming messages:

     import pika
     import simplejson

     # setup our variables
     address = 'localhost'
     exchange='barkingowl'

     # create our pika connection and channel
     reqcon = pika.BlockingConnection(pika.ConnectionParameters(host=address))
     reqchan = reqcon.channel()
     reqchan.exchange_declare(exchange=exchange,type='fanout')
    
     # Connect to the queue within the channel
     result = reqchan.queue_declare(exclusive=True)
     queue_name = result.method.queue
     reqchan.queue_bind(exchange=exchange,queue=queue_name)
    
     # attach a call back function to the queue
     reqchan.basic_consume(reqcallback,queue=queue_name,no_ack=True)

     # start consuming messages
     reqchan.start_consuming()

     # message handler
     def reqcallback(ch,method,properties,body):
         response = simplejson.loads(body)
         print "Message:\n\n\t{0}".format(response)

The above code will create a connection to the running RabbitMQ on 'localhost', begin listening to the 'barkingowl' exchange, and call the reqcallback function when a new message is available.  Now, one thing to note is that how this particular code is setup, all messages sent on the 'barkingowl' exchange will come to the reqcallback function.  Note that we set up a queue as well in the above code.  This queue will hold all the messages we get until we are ready to handle them.  This can be a blessing or *really* annoying depending on how you plan on using the message bus.  In the case here, we will be taking advantage of it since I will be writing the plugins as single threaded scripts (so the reqcallback will block until the task is complete).


**Sending Messages**

Now that we have the code to consume messages, we should write the code to publish them!

     import pika
     import simplejson

     # setup variables
     exchange = 'barkingowl'

     # setup outgoing messages
     respcon = pika.BlockingConnection(pika.ConnectionParameters(host=address))
     respchan = self._respcon.channel()
     respchan.exchange_declare(exchange=exchange,type='fanout')

     # create a message payload
     payload = {'command': 'url_payload', 'url': 'http://google.com/'}
     jbody = simplejson.dumps(payload)

     # publish the message to the message bus 
     respchan.basic_publish(exchange=exchange,routing_key='',body=jbody)

The last three lines of code ...

 - create the payload
 - serialize the payload to json
 - publish the payload to the Message Bus

... those will be an important part of the infrastructure of BarkingOwl.  One thing you will notice, however, is that there is not rigid structure requirement to the message body.  This is a good thing!  But what we need to do now is clearly, accurately, and concisely document the various payload formats that the system will support.

**The Message Format**

We will be using a standardized message format to allow each consumer to filter out only the types of messages they are interested in.

     # payload format
     payload = {
         'command': '',
         'sourceid': '',
         'destinationid': '',
         'message': '' 
     }

Let's take a look at each part of the payload:

 - Command
   - The command can be a number of things, but will define what the consumer will do with the rest of the payload.
   - Example Commands
     - 'url_payload' - the message portion of the payload will be a serialized object holding a URL and various meta data.

 - Source ID
   - The ID of the source of the message.  Each different part of the BarkingOwl system has a GUID (a global unique ID, more on this later).  This field holds the source of the message - although not always needed, it can be nice to know where you are getting the message from.

 - Destination ID
   - This is the intended destination ID for the message.  There is nothing within the system that prevents a consumer from receiving a message not intended for it, but that is by design.
   - This field would be used in the example of the Dispatcher responding to a Scraper coming online and broadcasting its availability.

 - Message
   - This is a bit of a catch-all field.  Anything else that the consumer may need to process the command correctly can be serialized in JSON format in this field.  In the example of the Dispatcher responding to a Scraper coming online, this would be the URL to scrape and it's meta data.

Now that we have the Message Bus, the Message Format defined, and some Python code talking to the bus and consuming messages, we can start writing the three remaining major parts of the BarkingOwl system: 1) Dispatcher, 2) Scraper, and 3) Archiver.  It would also be advantageous to write at least one plugin :p.

###What's Next###

Well, if you had taken a look, you'll see that there *IS* code written already - actually quite a lot of it.  What I have discovered is that the code base is getting a bit too large, and specifically the scraper got *RIDICULOUS* in size ha.  My goal of writing this post was to better identify the architecture to use, and how to split each part of the system.

The next step(s) will be to re-factor the existing code to fit the previously identified architecture.

Looking forward to working on the project this weekend, so hopefully another update soon!