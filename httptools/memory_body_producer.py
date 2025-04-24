# from zope.interface import implementer
# from twisted.web.iweb import IBodyProducer
# from twisted.internet.defer import succeed

# @implementer(IBodyProducer)
# class MemoryBodyProducer():
#     """
#     A BodyProducer that wraps a string into a BytesIO stream.
#     """

#     def __init__(self, body):
#         self.body = body # Convert string to bytes
#         self.length = len(self.body)

#     def startProducing(self, consumer):
#         consumer.write(self.body)
#         return succeed(None)

#     def pauseProducing(self):
#         pass

#     def stopProducing(self):
#         pass