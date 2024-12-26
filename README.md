# Passerelle DIS / HTTP.

## Généralités

Ce repository contient le nécessaire pour construire une passerelle DIS / HTTP.

La passerelle est construite sur la base de [Twisted](https://twisted.org/)
La partie DIS repose sur [open-dis-python](https://github.com/open-dis/open-dis-python).
Le repository contient le nécessaire pour construire des images docker contenant la passrelle.

## Architecture
### Traduction DIS vers HTTP:
Dans ce sens, on veut que la passerelle décode les messages DIS permettant de déterminer laposition des différentes plateformes,
et qu'elle les pousse via une API REST à une autre application.

Les messages DIS de type EntityStatePdu sont donc décodés, les positions transformées en position latitude et longitude, puis les
données sont transmise à un client HTTP qui les pousse en HTTP POST vers un serveur.

### Traduction HTTP vers DIS:
Dans ce sens, on veut que la passerelle récupère les instructions d'un autre serveur via une requête HTTP GET, puis qu'elle génère 
le ou les messages DIS nécessaires pour créér les instances nécessaires côté simulation.
Le but est notamment de générer des pistes missiles à la position, et avec la route et la vitesse indiquées par le serveur.

