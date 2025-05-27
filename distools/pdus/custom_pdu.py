from opendis.dis7 import Pdu
from opendis.DataOutputStream import DataOutputStream
from io import BytesIO


class CustomPdu(Pdu):
    def __init__(self):
        super().__init__()
        self.pduType = 140  # Unique identifier for this PDU type
        self.messages = []

    def add_message(self, message):
        """
        Add a message to the PDU.
        """
        print(f"[CustomPDU] adding message: {message}")
        self.messages.append(message)

    # def decode(self, data_stream):
    #     """
    #     Decode the binary data for this custom PDU.
    #     """
    #     super().decode(data_stream)  # Decode common PDU fields


    def serialize(self, outputStream):
        """
        Encode this PDU into binary format.
        """
        memoryStream = BytesIO()
        dummyoutputStream = DataOutputStream(memoryStream)

        super(CustomPdu, self).serialize(dummyoutputStream)
        for i, message in enumerate(self.messages):
            record_id = 1000 + i
            encoded = message.encode("utf-16-be")
            total_bits = (len(encoded) + 8) * 8  # 8 = 4 pour ID + 4 pour length
            dummyoutputStream.write_unsigned_int(record_id)  # Example: 4 bytes
            dummyoutputStream.write_unsigned_int(total_bits)  # Example: 4 bytes
            dummyoutputStream.stream.write(encoded)  # Write the encoded message


        # Ajout du padding à 8 octets
        if dummyoutputStream.stream.getbuffer().nbytes % 8 != 0:
            padding = 8 - (dummyoutputStream.stream.getbuffer().nbytes % 8)
            dummyoutputStream.stream.write(b"\x00" * padding) 

        # 1ère passe: on connait désormais la longueur finale du PDU.

        self.length = dummyoutputStream.stream.getbuffer().nbytes

        # 2ème passe: on réencode pour avoir le PDU avec la bonne longueur.
        super(CustomPdu, self).serialize(outputStream)
        for i, message in enumerate(self.messages):
            record_id = 1000 + i
            encoded = message.encode("utf-16-be")
            total_bits = (len(encoded) + 8) * 8  # 8 = 4 pour ID + 4 pour length
            outputStream.write_unsigned_int(record_id)  # Example: 4 bytes
            outputStream.write_unsigned_int(total_bits)  # Example: 4 bytes
            outputStream.stream.write(encoded)  # Write the encoded message


        # Ajout du padding à 8 octets
        outputStream.stream.write(b"\x00" * padding) 

    # def to_dict(self):
    #     """
    #     Convert the PDU to a JSON-serializable dictionary.
    #     """
    #     return {
    #         "pduType": self.pduType,
    #         "newOwner": self.newOwner,
    #         "transferReason": self.transferReason,
    #     }
