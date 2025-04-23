def pdu_to_dict(pdu_object):
    """
    Transforme un objet PDU en dictionnaire Python.
    Parcourt récursivement les attributs de l'objet.
    """
    result = {}
    for attribute in dir(pdu_object):
        if not attribute.startswith("_") and not callable(getattr(pdu_object, attribute)):
            value = getattr(pdu_object, attribute)
            if isinstance(value, list):
                # Si c'est une liste, applique la conversion à chaque élément
                result[attribute] = [pdu_to_dict(item) if hasattr(item, "__dict__") else item for item in value]
            elif attribute == "marking":
                result[attribute] = getattr(pdu_object, attribute).charactersString()
            elif hasattr(value, "__dict__"):
                # Si c'est un objet complexe, appelle récursivement
                result[attribute] = pdu_to_dict(value)
            else:
                result[attribute] = value
    return result