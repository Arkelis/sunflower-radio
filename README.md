# Radio Tournesol

Affiche les métadonnées de radio : Un serveur (flask) s'occupe d'aller chercher les métadonnées et expose une page de lecteur ainsi que des métadonnées. Ce serveur ne diffuse pas de radio. Il peut être utilisé en combinaison avec [liquidsoap](https://www.liquidsoap.info) pour l'encodage de la radio et [icecast2](http://icecast.org/) pour sa diffusion par exemple.

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

**Remarque :** Il faut respecter le format `<Debut>-<Fin> Station` avec le format `HH:MM:SS` (secondes facultatives) pour `<Debut>` et `<Fin>`.

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
