# Passerelle DIS / HTTP.

## Généralités

Ce repository contient le nécessaire pour construire une passerelle DIS / HTTP.

La passerelle est construite sur la base de [Twisted](https://twisted.org/) ainsi que du client HTTP [treq](https://treq.readthedocs.io/en/release-22.1.0/index.html)  
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

La génération d'un message EntityStatePdu suffit à initialiser le missile dans la situation entretenue par le poste Direct CGF de destination.

Les PDU connus par Direct CGF sont disponibles dans un fichiers Excel dans le dossier du logiciel (Resources/DIS).

Il faut donc consulter ce fichier pour obtenir les formats de messages reconnus par Direct CGF et à utiliser pour un transfert of ownership.

```                                        
                        HTTP_ENDPOINT_RECEIVER          HTTP_ENDPOINT_POLLER 
                        HTTP_BEARER_TOKEN_RECEIVER      HTTP_BEARER_TOKEN_POLLER
                                                        POLL_INTERVAL                                        
                                                          
                            HTTP RECEIVER API           HTTP POLLER API                  
                                        ▲                    ▲                     
                                        │                    │                     
                                    ┌─────────────────┐  ┌─────────────────┐          
                                    │                 │  │                 │          
                                    │   HTTP Poster   │  │    HTTP Poller  │          
                                    │                 │  │                 │          
                                    └─────────────────┘  └─────────────────┘          
                                        ▲                     │                         
                                        │ DIS PDU             │  Engagement            
                                        │ as dict             ▼  data (JSON)                 
                                                                                    
                                    ┌──────────────────────────────────────┐          
                                    │           DIS COMMUNICATOR           │               
DIS_RECEIVER_IP/PORT/MODE  DIS ────►│  DIS Receiver          DIS Emitter   │ ────► DIS     REMOTE_DIS_SITE
                                    │                                      │               DIS_EMITTER_IP/PORT/MODE
                                    └──────────────────────────────────────┘          
                                    ┌──────────────────────────────────────┐          
                                    │                                      │          
                                    │                app.py                │          
                                    │                                      │          
                                    └──────────────────────────────────────┘          
                                    ┌──────────────────────────────────────┐          
                                    │              config.py               │          
                                    └──────────────────────────────────────┘          
                                    ┌──────────────────────────────────────┐          
                                    │        environnement or .env         │          
                                    └──────────────────────────────────────┘          
```

### Entity ID des entités émises par la passerelle 

Les EntityID des EntityStatePDU émis par la passerelle sont définis ainsi:  
- Chaque EntityID est composé d'un Site Number (SN), un Application Number (AN) et un Entity Number (EN)
- Le SN est défini côté passerelle par la clé de configuration REMOTE_DIS_SITE
- l'AN est unique à chaque unité et est transmis par l'API
- l'EN est une valeur unique pour chaque PDU et est l'incrément d'un pool commun à toutes les unités. Il est transmis par l'API également
- Ainsi chaque EntityStatePDU est identifié par son équipe (SN), son unité (AN), et sa valeur unique (EN).

## Configuration
La configuration peut se faire par les variables d'environnement ou un fichier .env

Les variables suivantes sont utilisées:

### Dans le sens DIS vers HTTP:
DIS_RECEIVER_IP: adresse IP de destination des messages DIS (pour le cas multicast)  
DIS_RECEIVER_PORT: le port sur lequel attendre les messages DIS  
DIS_RECEIVER_MODE: peut être unicast, broadcast ou multicast  

Les messages DIS de type EntityState sont décodées, puis transmis à un endpoint REST déterminé par les paramètres suivants:  
HTTP_ENDPOINT_RECEIVER: l'url distante  
HTTP_BEARER_TOKEN_RECEIVER: le token à utiliser pour l'authentification  

### Dans le sens HTTP vers DIS:
HTTP_ENDPOINT_POLLER: url du endpoint à interroger  
HTTP_BEARER_TOKEN_POLLER: token à utiliser pour l'authentification  
POLL_INTERVAL: intervalle de poll (en secondes)  

Les engagements transmis par le serveur distant sont traités puis convertis en message EntityStatePdu qui est émis avec les paramètres ci-dessous:  

REMOTE_DIS_SITE: numéro du site auquel envoyer les messages DIS  

DIS_EMITTER_IP: adresse IP vers laquelle envoyer les messages DIS  
DIS_EMITTER_PORT: port de destination des messages DIS  
DIS_EMITTER_MODE: peut être unicast, broadcast ou multicast  

### Authentification
Si le même token doit être utilisé pour les 2 endpoint API (cas de'un seul serveur exposant les 2 endpoint par exemple), il est possible de renseigner le token dans la variable HTTP_BEARER_TOKEN.  
Il sera alors utilisé pour les 2.

### Certificats SSL
Une whitelist de domaines dont le certificat n'est pas vérifié est générée à partir des domaines configurés dans HTTP_ACK_ENDPOINT et HTTP_ENDPOINT_POLLER

## Mode Standalone

Le script batch [build_portable_version.bat](build_portable_version.bat) permet de générer une version standalone du logiciel.  
En voici les étapes:
- Télécharge la version 3.10 de WinPython et en extrait le contenu
- Télécharge et installe les requirements du projet dans cet environnement
- Supprime le contenu superflu de WinPython (optimisable)
- Créé un dossier pour la version portable du projet contenant cet environnement et l'application en excluant les fichiers et dossiers superflus (optimisable également)
- Génère un .bat d'exécution de l'application
- Compresse le tout (Actuellement commenté car plus long qu'une compression manuelle, mais présent si nécessaire)

## Tests

Des tests unitaires sont présents afin de tester les méthodes [missile.advance()](simtools\objects.py) et [ECEF_to_natural_velocity()/natural_velocity_to_ECEF()](distools\geotools\test\test_tools.py).  
Ils utilisent le module [unittest de Twisted](https://docs.twisted.org/en/stable/development/test-standard.html) et il est possible de les exécuter depuis la racine du projet à l'aide de:
```sh
python -m twisted.trial distools.geotools simtools # Afin d'exécuter les deux groupes de tests
python -m twisted.trial distools.geotools.test.test_tools.velocityTestCase.test_velocity_west # Afin de n'exécuter qu'un test spécifique, ici test_velocity_west
```
pour n'exécuter qu'un test spécifique, ici `test_velocity_west` par exemple