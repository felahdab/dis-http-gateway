from opendis.dis7 import VariableDatum
import struct

# Voir SISO-REF010 page 725 pour les ID des Datums correspondants.

class FloatAs4BytesDatum(VariableDatum):
    def __init__(self, datumID, value):
        super(FloatAs4BytesDatum, self).__init__(datumID, 8*8, struct.pack('>d', value))

class IntAs1ByteDatum(VariableDatum):
    def __init__(self, datumID, value):
        super(IntAs1ByteDatum, self).__init__(datumID, 8*1, struct.pack('>B', value))

class IntAs2ByteDatum(VariableDatum):
    def __init__(self, datumID, value):
        super(IntAs2ByteDatum, self).__init__(datumID, 8*2, struct.pack('>H', value))

class EntityLocationDatum(FloatAs4BytesDatum):
    def __init__(self, coordinate, value):
        if coordinate not in ["X", "Y", "Z"]:
            raise Exception("Invalid coordinate for EntityLocationDatum class")
        value=float(value)
        if coordinate == "X":
            self.datumID=240017
        elif coordinate == "Y":
            self.datumID=240018
        elif coordinate == "Z":
            self.datumID=240019
        super(EntityLocationDatum, self).__init__(self.datumID,  value)

class EntityLinearVelocityDatum(FloatAs4BytesDatum):
    def __init__(self, coordinate, value):
        if coordinate not in ["X", "Y", "Z"]:
            raise Exception("Invalid coordinate for EntityLinearVelocityDatum class")
        value=float(value)
        if coordinate == "X":
            self.datumID=240020
        elif coordinate == "Y":
            self.datumID=240021
        elif coordinate == "Z":
            self.datumID=240022
        super(EntityLinearVelocityDatum, self).__init__(self.datumID,  value)

class EntityOrientationDatum(FloatAs4BytesDatum):
    def __init__(self, coordinate, value):
        if coordinate not in ["psi", "theta", "phi"]:
            raise Exception("Invalid coordinate for EntityLinearVelocityDatum class")
        value=float(value)
        if coordinate == "psi":
            self.datumID=240023
        elif coordinate == "theta":
            self.datumID=240024
        elif coordinate == "phi":
            self.datumID=240025
        super(EntityOrientationDatum, self).__init__(self.datumID,  value)

class EntityKindDatum(IntAs1ByteDatum):
    def __init__(self, value):
        super(EntityKindDatum, self).__init__(11110, value)

class EntityDomainDatum(IntAs1ByteDatum):
    def __init__(self, value):
        super(EntityDomainDatum, self).__init__(11120, value)

class EntityCountryDatum(IntAs2ByteDatum):
    def __init__(self, value):
        super(EntityCountryDatum, self).__init__(11130, value)

class EntityCategoryDatum(IntAs1ByteDatum):
    def __init__(self, value):
        super(EntityCategoryDatum, self).__init__(11140, value)

class EntitySubCategoryDatum(IntAs1ByteDatum):
    def __init__(self, value):
        super(EntitySubCategoryDatum, self).__init__(11150, value)

class EntitySpecificDatum(IntAs1ByteDatum):
    def __init__(self, value):
        super(EntitySpecificDatum, self).__init__(11160, value)

class EntityExtraDatum(IntAs1ByteDatum):
    def __init__(self, value):
        super(EntityExtraDatum, self).__init__(11170, value)