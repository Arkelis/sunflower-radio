# Radio Tournesol

Ce programme a deux vocations :
- Afficher les métadonnées d'une radio en cours de lecture sur une page avec un lecteur.
- Exposer en json les métadonnées.
- Interagir avec un server telnet [liquidsoap](https://www.liquidsoap.info)

Grâce à liquidsoap, on peut changer la station diffusée au cours de la journée, d'où le nom Radio Tournesol.

## Principe

Une webradio est composé de divers éléments :

- un encodeur de flux audio, par exemple liquidsoap
- un diffuseur de flux audio, par exemple icecast
- un client de lecture (cette application !)

Radio tournesol a donc pour principale vocation d'afficher les métadonnées de la radio en cours de lecture. Cependant, grâce au serveur telnet de liquidsoap, Radio tournesol peut aussi interagir avec celui-ci ; cela permet d'étendre les possibilités : par exemple Radio tournesol peut détecter de la publicité et donc demander à liquidsoap de jouer de la musique à la place.

En plus d'être un client de lecture, Radio Tournesol participe donc aussi à l'encodage de flux audio.

## Fonctionnement de Radio Tournesol

### Client de lecture

Le client de lecture se présente sous forme d'un serveur Flask. Celui-ci s'appuie sur deux types d'objets :

#### Radio

Elle est composée de stations. Elle va puiser les métadonnées chez les stations enregistrées. Pour savoir à quelle station elle doit s'adresser, elle s'appuie sur un fichier de configuration (cf. paragraphe **Configuration** plus bas).

#### Station

Une station représente une station jouée sur une plage horaire. Elle doit implémenter deux méthodes (`get_metadata()` et `format_info()`) pour alimenter la radio et le serveur Flask.

### Watcher

Les métadonnées sont stockées sur le serveur dans la mémoire grâce à Redis. Elles sont récupérées par un watcher lancé en démon grâce à Daemonize.

## Installation

```
$ poetry install 
```

Il faut [poetry](https://github.com/sdispater/poetry).

## Configuration

Vous devez créer une liste de plages horaires dans `settings.py` (au même niveau que `radio.py`). Ce fichier
permet de savoir quelle radio inspecter en fonction de l'heure. Exemple :

```python
TIMETABLE = [
    # (start, end, station_name),
    ("00:00", "06:00", "France Inter"),
    ("06:00", "07:00", "France Info"),
    ("07:00", "09:00", "France Inter"),
    ("09:00", "13:00", "RTL 2"),
    ("13:00", "14:00", "France Inter"),
    ("14:00", "19:00", "RTL 2"),
    ("19:00", "20:00", "France Inter"),
    ("20:00", "21:00", "France Info"),
    ("21:00", "00:00", "RTL 2"),
]
```

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
- Aller à `localhost:8080/on-air` pour accéder métadonnées au format json du programme en cours.

## Feuille de route
 
- [x] Mise à jour des champs en temps réel
- [ ] Jingles horaires et de transition
- [ ] Mettre une musique à la place de la pub pour RTL 2
- [x] Rendre la page du lecteur responsive
- [ ] Thème sombre
- [ ] Faire de la page du lecteur une PWA
- [ ] Faire du projet une lib
