from opendis import PduFactory
from pdus.transfer_ownership_pdu import TransferOwnershipPdu

# Save the original create_pdu method
original_create_pdu = PduFactory.createPdu

def extended_create_pdu(data):
    """
    Custom PDU Factory logic to handle unsupported PDU types.
    """
    pdu_type = data[2]  # The index 2 typically contains the PDU type in DIS format
    if pdu_type == 35:  # Unique identifier for TransferOwnershipPdu
        pdu = TransferOwnershipPdu()
        pdu.decode(data)
        return pdu

    # Call the original method for all other PDUs
    return original_create_pdu(data)

# Patch PduFactory
def extend_pdu_factory():
    PduFactory.createPdu = extended_create_pdu
