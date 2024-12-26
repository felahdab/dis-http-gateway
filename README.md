# Passerelle DIS / HTTP.

## Généralités

Ce repository contient le nécessaire pour construire une passerelle DIS / HTTP.

La passerelle est construite sur la base de [Twisted](https://twisted.org/)
La partie DIS repose sur [open-dis-python](https://github.com/open-dis/open-dis-python).
Le repository contient le nécessaire pour construire des images docker contenant la passerelle.

## Architecture
### Traduction DIS vers HTTP:
Dans ce sens, on veut que la passerelle décode les messages DIS permettant de déterminer la position des différentes plateformes,
et qu'elle les pousse via une API REST à une autre application.

Les messages DIS de type EntityStatePdu sont donc décodés, les positions transformées en position latitude et longitude, puis les
données sont transmise à un client HTTP qui les pousse en HTTP POST vers un serveur.

### Traduction HTTP vers DIS:
Dans ce sens, on veut que la passerelle récupère les instructions d'un autre serveur via une requête HTTP GET, puis qu'elle génère 
le ou les messages DIS nécessaires pour créér les instances nécessaires côté simulation.
Le but est notamment de générer des pistes missiles à la position, et avec la route et la vitesse indiquées par le serveur.

Dans ce mode, on souhaite que la passerelle transmette à Direct-CGF les messages DIS permettant d'initialiser une nouvelle Entity (correspondant au missile) à la position de tir (la position de l'unité tireuse), avec une route cohérente avec la piste sur laquelle tire l'unité, et une vitesse cohérente avec le type d'armement. La position, la route et la vitesse seront fournies par la requête HTTP.
Après avoir initialiser le missile tiré, la passerelle doit initier un changement de propriété (Ownership) afin que DirectCGF se charge de faire "vivre" le missile.

Remarque: le "Ownership management" ne fonctionne qu'en DIS 6 et 7 (manuel Direct CGF, page 600)

Le ownership management nécessite les messages de type TransferControlRequestPdu (PduType == 35) qui n'est pas implémenté dans OpenDIS. La succession des messages nécessaires est décrit en annexe H de l'IEEE 1278-200X draft 16 rev 18.pdf.
Le transfert d'ownership peut être rendu automatique: manuel Direct CFG, page 605.

Les PDU connus par Direct CGF sont disponibles dans un fichiers Excel dans le dossier du logiciel (Resources/DIS).

Il faut donc consulter ce fichier pour obtenir les formats de messages reconnus par Direct CGF et à utiliser pour un transfert of ownership.