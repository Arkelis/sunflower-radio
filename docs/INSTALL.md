# Installation de Radio Tournesol

## Composants Python : Radio et Serveur

Les composants suivants sont écrits en Python :

- La gestion de la radio (dossier `sunflower`)
- Le serveur de l'API exposant les informations (dossier `server`)

Le projet nécessite Python 3.8 ou supérieur, il est recommandé d'utiliser
[`pyenv`](https://github.com/pyenv/pyenv) pour gérer les différentes
installations de Python.

Pour installer les dépendances, il est recommandé (et pour l'instant nécessaire)
d'utiliser [`poetry`](https://github.com/python-poetry/poetry).

```
poetry install
```

## Composant encodeur de flux radio : Liquidsoap

Pour encoder le flux radio, il faut installer 
[Liquidsoap](https://github.com/savonet/liquidsoap).
Ce composant est  écrit en OCaml.

Il est recommandé d'utiliser [`opam`](http://opam.ocaml.org/) pour gérer les
installations d'OCaml.

Pour installer Liquidsoap et les différents modules nécessaires au traitement
des fichiers audio :

```
opam depext taglib mad vorbis cry opus samplerate faad liquidsoap
opam install taglib mad vorbis cry opus samplerate faad liquidsoap
```

Ces modules sont spécifiques à Radio Pycolore, on peut en installer d'autres pour
gérer d'autres formats audio.

Une fois le composant installé, il faut générer la configuration Liquidsoap :

```
poetry run make generate-liquidsoap-config
```

## Composant de diffusion de flux : Icecast

Liquidsoap est configuré pour envoyer les flux audio sur [Icecast](https://icecast.org). Il est donc
nécessaire d'installer Icecast au préalable.

## Redis

Pour persister des données temporairement, Radio Tournesol utilise la base de
données Redis. Il est nécessaire de l'installer et de démarrer le serveur Redis
avant de démarrer la radio.

## Configuration

Le fichier `sunflower/settings.py` contient différentes variables qui vont être
utilisées par le projet.

* `ICECAST_SERVER_URL` : L'url du serveur Icecast, utilisée par Liquidsoap.
* `CHANNELS` : Liste des endpoints des chaînes définies. Nécessaire pour faire
  diverses vérifications.
* `BACKUP_SONGS_GLOB_PATTERN`: Chemin vers le dossier des chansons utilisées par
  la playlist Pycolore.
* `LIQUIDSOAP_TELNET_PORT` : Port à utiliser pour se connecter au server telnet
  de Liquidsoap.
* `LIQUIDSOAP_TELNET_HOST` : Hôte à utiliser pour se connecter au serveur telnet 
  de Liquidsoap.
