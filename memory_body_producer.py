from twisted.web.iweb import IBodyProducer
from twisted.internet.defer import succeed
import io


class MemoryBodyProducer(IBodyProducer):
    """
    A BodyProducer that wraps a string into a BytesIO stream.
    """

    def __init__(self, content):
        self.content = content.encode("utf-8")  # Convert string to bytes
        self.length = len(self.content)
        self._buffer = io.BytesIO(self.content)

    def startProducing(self, consumer):
        consumer.write(self._buffer.read())
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        self._buffer.close()