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

La génération d'un message EntityStatePdu suffit à initialiser le missile dans la situation entretenue par le poste Direct CGF de destination.

Les PDU connus par Direct CGF sont disponibles dans un fichiers Excel dans le dossier du logiciel (Resources/DIS).

Il faut donc consulter ce fichier pour obtenir les formats de messages reconnus par Direct CGF et à utiliser pour un transfert of ownership.

                                        
                        HTTP_ENDPOINT_RECEIVER          HTTP_ENDPOINT_POLLER 
                        HTTP_BEARER_TOKEN_RECEIVER      HTTP_BEARER_TOKEN_POLLER
                                                        POLL_INTERVAL                                        
                                                          
                            HTTP RECEIVER API           HTTP POLLER API                  
                                        ▲                    ▲ │                    
                                        │                    │ │                    
                                    ┌─────┴───────────┐  ┌─────┴─▼─────────┐          
                                    │                 │  │                 │          
                                    │   HTTP Poster   │  │  poll_api       │          
                                    │                 │  │                 │          
                                    └─────────────────┘  └─────────────────┘          
                                        ▲                                              
                                        │ DIS Pdu             │  Engagement            
                                        │ as dict             ▼  data                  
                                                                                    
                                    ┌─────────────────┐  ┌─────────────────┐          
                                    │                 │  │                 │               OWN_DIS_SITE / OWN_DIS_APPLICATION
DIS_RECEIVER_IP/PORT/MODE  DIS ────►│  DIS Receiver   │  │   DIS Emitter   │ ────► DIS     REMOTE_DIS_SITE / REMOTE_DIS_APPLICATION
                                    │                 │  │                 │               DIS_EMITTER_IP/PORT/MODE
                                    └─────────────────┘  └─────────────────┘          
                                    ┌──────────────────────────────────────┐          
                                    │                                      │          
                                    │                app.py                │          
                                    │                                      │          
                                    └──────────────────────────────────────┘          
                                    ┌──────────────────────────────────────┐          
                                    │              config.py               │          
                                    └──────────────────────────────────────┘          
                                    ┌──────────────────────────────────────┐          
                                    │          environnement or .env       │          
                                    └──────────────────────────────────────┘          

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

OWN_DIS_SITE: numéro de site local à utiliser lors de l'envoi de messages DIS
OWN_DIS_APPLICATION: numéro de l'application locale à utiliser lors de l'envoi de messages DIS
REMOTE_DIS_SITE: numéro du site auquel envoyer les messages DIS
REMOTE_DIS_APPLICATION: numéro de l'application distante à laquelle envoyer les messages DIS

DIS_EMITTER_IP: adresse IP vers laquelle envoyer les messages DIS
DIS_EMITTER_PORT: port de destination des messages DIS
DIS_EMITTER_MODE: peut être unicast, broadcast ou multicast

### Authentification
Si le même token doit être utilisé pour les 2 endpoint API (cas de'un seul serveur exposant les 2 endpoint par exemple), il est possible de renseigner le token dans la variable HTTP_BEARER_TOKEN.
Il sera alors utilisé pour les 2.

### Certificats SSL
Le paramètre HTTP_IGNORE_CERT permet de préciser si on veut ignorer les certificats SSL invalides (par exemple les certificats auto signés)