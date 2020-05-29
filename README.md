# Radio Tournesol

[![Python 3.8](https://img.shields.io/badge/Python-3.8-blue)](https://python.org) [![Tests](https://github.com/Arkelis/sunflower-radio/workflows/Tests/badge.svg?branch=master)](https://github.com/Arkelis/sunflower-radio/actions?query=workflow%3ATests)

## Principe

Une webradio est composé de divers éléments :

- un encodeur de flux audio, par exemple [liquidsoap](http://liquidsoap.info)
- un diffuseur de flux audio, par exemple [icecast](http://icecast.org/)
- un client de lecture

Radio Tournesol s'insère dans deux de ces éléments :

- l'encodage : le programme génère, à partir d'un planning, la configuration pour liquidsoap qui changer de chaîne en fonction des horaires. De plus un *scheduler* surveille les publicités et demande à liquidsoap de jouer de la musique à la place de la station s'il en détecte ;
- le client de lecture : Radio Tournesol propose sa propre interface web ainsi qu'une API exposant des données.

## Fonctionnement de Radio Tournesol

### Client de lecture

Le client de lecture se présente sous forme d'un serveur Flask. Celui-ci s'appuie sur deux types d'objets :

#### Channel

Elle est composée de stations. Elle va puiser les métadonnées chez les stations enregistrées. Lors de son instanciation, on indique les stations utilisées, son nom (qui sera aussi son endpoint), ainsi que sa table d'horaires. Par exemple, la chaîne Tournesol de Radio Pycolore est définie comme suit :

```python
tournesol = Channel(
    endpoint="tournesol",
    stations=(FranceCulture, FranceInter, FranceMusique, FranceInfo, RTL2),
    timetable={
        # (weekday1, weekday2, ...)
        (0, 1, 2, 3, 4): [
            # (start, end, station_name),
            ("00:00", "05:00", FranceCulture), # Les nuits de France Culture
            ("05:00", "07:00", FranceInfo), # Matinale
            ("07:00", "09:00", FranceInter), # Matinale
            ("09:00", "11:00", RTL2), # Musique
            ("11:00", "12:00", FranceCulture), # Toute une vie
            ("12:00", "15:00", FranceInter), # Jeu des mille, journal, boomerang
            ("15:00", "18:00", FranceCulture), # La compagnie des auteurs/poètes, La Méthode scientifique, LSD (la série docu)
            ("18:00", "20:00", FranceInter), # Soirée
            ("20:00", "21:00", FranceInfo), # Les informés
            ("21:00", "00:00", RTL2), # Musique
        ],
        (5,): [
            ("00:00", "06:00", FranceCulture), # Les nuits de France Culture
            ("06:00", "07:00", FranceInfo), # Matinale
            ("06:00", "09:00", FranceInter), # Matinale
            ("09:00", "11:00", RTL2), # Musique
            ("11:00", "14:00", FranceInter), # Sur les épaules de Darwin + politique + midi
            ("14:00", "17:00", FranceCulture), # Plan large, Toute une vie, La Conversation scientifique
            ("17:00", "18:00", FranceInter), # La preuve par Z avec JF Zygel
            ("18:00", "20:00", FranceInter), # Tel sonne spécial corona
            ("20:00", "21:00", FranceInfo), # Les informés
            ("21:00", "00:00", FranceCulture), # Soirée Culture (Fiction, Mauvais Genre, rediff Toute une vie)
        ],
        (6,): [
            ("00:00", "07:00", FranceCulture), # Les nuits de France Culture
            ("07:00", "09:00", FranceInter), # Matinale
            ("09:00", "12:00", RTL2),
            ("12:00", "14:00", FranceInter), # Politique + journal
            ("14:00", "18:00", FranceMusique), # Aprem Musique : Carrefour de Lodéon et La tribune des critiques de disques
            # ("18:00", "19:00", RTL2),
            ("18:00", "21:00", FranceInter), # Spécial Corona : téléphone sonne et le masque et la plume
            ("21:00", "00:00", RTL2),
        ]
    },
)
```

#### Station

Une station représente une station jouée sur une plage horaire. Elle doit implémenter deux méthodes (`get_metadata()` et `format_info()`) pour alimenter la radio et le serveur Flask.

### Scheduler

Les métadonnées sont stockées sur le serveur dans la mémoire grâce à Redis. Elles sont récupérées par un scheduler lancé en démon grâce à Daemonize.

## Installation

```
$ poetry install 
```

Il faut [poetry](https://github.com/sdispater/poetry).

## Configuration

Le fichier `settings.py` contient trois éléments :
- l'url du serveur icecast
- le chemin vers le dossier contenant les musiques à jouer en cas de pub ;
- les noms des chaînes créées dans `channels.py`

**Radio supportées :**

- France Inter
- France Musique
- France Culture
- France Info
- RTL 2

## Test

```
$ poetry run flask run
```

- Aller à `localhost:8080` pour accéder au client de lecture.
- Aller à `localhost:8080/api` pour accéder aux données exposées en JSON.

## Feuille de route
 
- [x] Mise à jour des champs en temps réel
- [ ] Jingles horaires et de transition
- [x] Mettre une musique à la place de la pub pour RTL 2
- [x] Rendre la page du lecteur responsive
- [x] Thème sombre
- [ ] Faire de la page du lecteur une PWA
- [ ] Faire du projet une lib
