# Radio Tournesol

Affiche les métadonnées de radio.

## Installation

```
$ poetry install 
```

Il faut [poetry](https://github.com/sdispater/poetry).

## Configuration

Vous devez créer un fichier d'horaires pour les radios `timetable.conf` (au même niveau que `radio.py`. Ce fichier
permet de savoir quelle radio inspecter en fonction de l'heure. Exemple :

```
00:00-06:00 France Inter
06:00-07:00 France Info
07:00-09:00 France Inter
09:00-13:00 RTL 2
13:00-14:00 France Inter
13:00-19:00 RTL 2
19:00-20:00 France Inter
20:00-21:00 France Info
21:00-00:00 RTL 2
```

**Remarque :** Il faut respecter le format `HH:MM:[SS] Station` (secondes facultatives).

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

Aller à `localhost:8000` pour voir les métadonnées de la radio en cours.
