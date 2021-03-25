<p align="center">
   <img src="https://www.pycolore.fr/assets/img/sunflower-logo-min.png" alt="Logo" width=200 height=200>
</p>


# Radio Tournesol

[![Python 3.8](https://img.shields.io/badge/Python-3.8-blue)](https://python.org) [![Tests](https://github.com/Arkelis/sunflower-radio/workflows/Tests/badge.svg?branch=devel)](https://github.com/Arkelis/sunflower-radio/actions?query=workflow%3ATests)

## Principe

Une webradio est composé de divers éléments :

- un encodeur de flux audio, par exemple [liquidsoap](http://liquidsoap.info)
- un diffuseur de flux audio, par exemple [icecast](http://icecast.org/)
- un client de lecture

Radio Tournesol s'insère dans deux de ces éléments :

- l'encodage : le programme génère, à partir d'un planning, la configuration pour liquidsoap qui changer de chaîne en fonction des horaires. De plus un *scheduler* surveille les publicités et demande à liquidsoap de jouer de la musique à la place de la station s'il en détecte ;
- le client de lecture : Radio Tournesol propose [sa propre interface web](https://github.com/Arkelis/sunflower-webapp) ainsi qu'une API exposant des données.

## Fonctionnement de Radio Tournesol

### Scheduler

Un planificateur (`Scheduler`) s'occupe de gérer des objets chaînes `Channel` qui contiennent des références vers les
stations utilisées. À intervalle de temps régulier, il appelle une méthode `process()` de ces objets qui va lancer
des traitements, par exemple pour aller chercher les informations sur le programme en cours de diffusion.

#### Channel

Elle est composée de stations. Elle va puiser les métadonnées chez les stations enregistrées. Lors de son instanciation,
on indique les stations utilisées, son nom (qui sera aussi son endpoint), ainsi que sa table d'horaires. Par exemple
la chaîne Tournesol de Radio Pycolore est définie comme suit :

```python
tournesol = Channel(
    endpoint="tournesol",
    handlers=(AdsHandler,),
    timetable={
        # (weekday1, weekday2, ...)
        (0, 1, 2, 3, 4): [
            # (start, end, station_name),
            ("00:00", "05:00", FranceCulture),
            ("05:00", "07:00", FranceInfo),
            ("07:00", "10:00", FranceInter),
            ("10:00", "11:00", PycolorePlaylistStation),
            ("11:00", "12:00", FranceCulture),
            ("12:00", "14:00", FranceInter),
            ("14:00", "18:00", FranceCulture),
            ("18:00", "20:00", FranceInter),
            ("20:00", "21:00", FranceInfo),
            ("21:00", "22:00", RTL2),
            ("22:00", "00:00", PycolorePlaylistStation),
        ],
        (5,): [
            ("00:00", "06:00", FranceCulture),
            ("06:00", "09:00", FranceInter),
            ("09:00", "11:00", PycolorePlaylistStation),
            ("11:00", "14:00", FranceInter),
            ("14:00", "17:00", FranceCulture),
            ("17:00", "18:00", FranceInter),
            ("18:00", "20:00", FranceInter),
            ("20:00", "21:00", FranceInfo),
            ("21:00", "00:00", FranceCulture),
        ],
        (6,): [
            ("00:00", "06:00", FranceCulture),
            ("06:00", "09:00", FranceInter),
            ("09:00", "11:00", PycolorePlaylistStation),
            ("11:00", "14:00", FranceInter),
            ("14:00", "18:00", FranceMusique),
            # ("18:00", "19:00", RTL2),
            ("18:00", "21:00", FranceInter),
            ("21:00", "22:00", RTL2),
            ("22:00", "00:00", PycolorePlaylistStation),
        ]
    },
)
```

Dans cet exemple, `tournesol` fait appel à un `Handler`, une classe qui altère les métadonnées une fois qu'elles ont
été récupérées par la station.

#### Station

Une station représente une station diffusée sur une plage horaire. Elle doit implémenter quatre méthodes pour alimenter la radio et l'API.

* `get_step()` : cette méthode va chercher les informations sur le programme en cours de diffusion. Par exemple
  , pour une station telle que France Inter, elle va utiliser l'API de Radio France.
* `get_next_step()` : idem, mais pour le programme suivant.
* `get_schedule()` : renvoie une liste de programme pour une plage de temps donnée.
* `format_stream_metadata()` : cette méthode formate des métadonnées pour les envoyer à l'encodeur qui va les inclure
  dans le flux audio. Elles sont lues par les lecteurs audio.

### Client de lecture

Si l'on peut écouter la radio simplement à partir du flux généré par Liquidsoap,
il existe aussiun projet d'interface web pour écouter les radios et accéder aux
différents programmes depuis le navigateur&nbsp;: 
[Sunflower Webapp](https://github.com/Arkelis/sunflower-webapp).

## Contribuer

Vous pouvez cloner le projet pour le tester ou proposer des modifications:

```
$ git clone https://github.com/Arkelis/sunflower-radio
```

### Installation des dépendances

Les différents composants à installer sur sa machine pour démarrer le projet
sont détaillés dans la page [INSTALL.md](docs/INSTALL.md).

## Déploiement

Le fichier [DEPLOY.md](docs/DEPLOY.md) expose la démarche à suivre pour déployer Radio Pycolore
sur un serveur Debian 10 Buster.

## Feuille de route

Voir les [milestones](https://github.com/Arkelis/sunflower-radio/milestones).
 
- [x] Mise à jour des champs en temps réel
- [ ] ~Jingles horaires et de transition~
- [x] Mettre une musique à la place de la pub pour RTL 2
- [x] Rendre la page du lecteur responsive
- [x] Thème sombre
- [ ] ~Faire de la page du lecteur une PWA~
- [ ] Faire du projet une lib
