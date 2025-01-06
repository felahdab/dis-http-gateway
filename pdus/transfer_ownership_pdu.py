from opendis.dis7 import Pdu

# Ce type de PDU n'est pas implémenté dans OpenDIS.
# On réalise donc une implémentation complémentaire, sur la base de l'IEEE 1278.1-200X Draft 16 rev 18, annexe H pour 
# l'usage qui en est fait et page 426 pour le contenu.  
# A confronter au format des messages attendus par DCGF.

class TransferOwnershipPdu(Pdu):
    def __init__(self):
        super().__init__()
        self.newOwner = 0
        self.transferReason = ""
        self.pduType = 35  # Unique identifier for this PDU type

    def decode(self, data_stream):
        """
        Decode the binary data for this custom PDU.
        """
        super().decode(data_stream)  # Decode common PDU fields
        self.newOwner = data_stream.read_int()  # Example: 4 bytes
        self.transferReason = data_stream.read_string()  # Example: Variable-length string

    def encode(self):
        """
        Encode this PDU into binary format.
        """
        data_stream = super().encode()  # Encode common PDU fields
        data_stream.write_int(self.newOwner)  # Example: 4 bytes
        data_stream.write_string(self.transferReason)  # Example: Variable-length string
        return data_stream

    def to_dict(self):
        """
        Convert the PDU to a JSON-serializable dictionary.
        """
        return {
            "pduType": self.pduType,
            "newOwner": self.newOwner,
            "transferReason": self.transferReason,
        }
