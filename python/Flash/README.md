# Message Flashing
- Every good application must provide a way to give users feedback. 
Flask provides a simple way to do that using the flashing system.<br>

- The flashing system makes it possible to record a message at the end of a request and is accessed on the next request(and only the next request)
- To flash a amessage use flash(), to get hold of message use 
get_flashed_mesages() also available in templates. 

## Logging
Sometimes we might be in a situation where you deal with data that should be correct, we might have some client-sidecode that sends an HTTP-Request to a server but is obviously malformed. you may still want to log something fishy that happened. <br>

    app.logger.warning("A value for debugging")
    app.logger.warning("A warning error (%d apples)",42)
    app.logger.warning("an error occurred")

[Link Text][id]

[id]: https://docs.python.org/library/logging.html "Optional Title"
    