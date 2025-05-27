from opendis.dis7 import Pdu

class CustomPdu(Pdu):
    def __init__(self):
        super().__init__()
        self.pduType = 140  # Unique identifier for this PDU type
        self.messages = []

    def add_message(self, message):
        """
        Add a message to the PDU.
        """
        self.messages.append(message)

    # def decode(self, data_stream):
    #     """
    #     Decode the binary data for this custom PDU.
    #     """
    #     super().decode(data_stream)  # Decode common PDU fields


    def encode(self):
        """
        Encode this PDU into binary format.
        """
        data_stream = super().encode()  # Encode common PDU fields
        for i, message in enumerate(self.messages):
            record_id = 1000 + i
            encoded = message.encode("utf-16-be")
            total_bits = (len(encoded) + 8) * 8  # 8 = 4 pour ID + 4 pour length
            data_stream.write_unsigned_int(record_id)  # Example: 4 bytes
            data_stream.write_unsigned_int(total_bits)  # Example: 4 bytes
            data_stream.stream.write(encoded)  # Write the encoded message


        # Ajout du padding à 8 octets
        if self.stream.getBuffer().nbytes % 8 != 0:
            padding = 8 - (self.stream.getBuffer().nbytes % 8)
            data_stream.stream.write(b"\x00" * padding) 

        # 1ère passe: on connait désormais la longueur finale du PDU.

        self.pduLength = self.stream.getBuffer().nbytes

        # 2ème passe: on réencode pour avoir le PDU avec la bonne longueur.
        data_stream = super().encode()  # Encode common PDU fields
        for i, message in enumerate(self.messages):
            record_id = 1000 + i
            encoded = message.encode("utf-16-be")
            total_bits = (len(encoded) + 8) * 8  # 8 = 4 pour ID + 4 pour length
            data_stream.write_unsigned_int(record_id)  # Example: 4 bytes
            data_stream.write_unsigned_int(total_bits)  # Example: 4 bytes
            data_stream.stream.write(encoded)  # Write the encoded message


        # Ajout du padding à 8 octets
        if self.stream.getBuffer().nbytes % 8 != 0:
            padding = 8 - (self.stream.getBuffer().nbytes % 8)
            data_stream.stream.write(b"\x00" * padding) 

        return data_stream

    # def to_dict(self):
    #     """
    #     Convert the PDU to a JSON-serializable dictionary.
    #     """
    #     return {
    #         "pduType": self.pduType,
    #         "newOwner": self.newOwner,
    #         "transferReason": self.transferReason,
    #     }
