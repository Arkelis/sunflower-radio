# This file is part of sunflower package. Radio app.

"""Module containing radio metadata fetching related functions."""

from sunflower.core.bases import Channel
from sunflower.handlers import AdsHandler
from sunflower.stations import (FranceCulture, FranceInfo, FranceInter, FranceMusique, PycolorePlaylistStation, RTL2)

tournesol = Channel(
    endpoint="tournesol",
    handlers=(AdsHandler,),
    timetable={
        # (weekday1, weekday2, ...)
        (0, 1, 2, 3, 4): [
            # (start, end, station_name),
            ("00:00", "05:00", FranceCulture), # Les nuits de France Culture
            ("06:00", "09:00", FranceInter), # Matinale
            ("09:00", "12:00", FranceCulture), # Le Cours de l'Histoire, les chemins de la philosophie, Toute une vie
            ("12:00", "12:30", FranceInfo), # Info
            ("12:30", "13:30", FranceInter), # Carnets de campagne, Jeu des mille, Journal
            ("13:30", "18:00", FranceCulture), # Les pieds sur terre, Entendez vous l'éco, compagnie des oeuvres, la méthode scientifique, LSD (La série documentaire)
            ("18:00", "20:00", FranceInter), # Le 18/20 de France Inter
            ("20:00", "00:00", FranceInfo), # Les informés, info
        ],
        (5,): [
            ("00:00", "06:00", FranceCulture), # Les nuits de France Culture
            ("06:00", "09:00", FranceInter), # Matinale
            ("09:00", "11:00", FranceInfo), # Info
            ("11:00", "14:00", FranceInter), # On va déguster
            ("14:00", "17:00", FranceCulture), # Plan large, Toute une vie, La Conversation scientifique
            ("17:00", "18:00", FranceInter), # La preuve par Z avec JF Zygel
            ("18:00", "20:00", FranceInter), # Tel sonne spécial corona
            ("20:00", "21:00", FranceInfo), # Les informés
            ("21:00", "00:00", FranceCulture), # Soirée Culture (Fiction, Mauvais Genre, rediff Toute une vie)
        ],
        (6,): [
            ("00:00", "06:00", FranceCulture), # Les nuits de France Culture
            ("06:00", "09:00", FranceInter), # Matinale
            ("09:00", "11:00", FranceInfo),
            ("11:00", "14:00", FranceInter), # On va déguster, politique, journal
            ("14:00", "18:00", FranceMusique), # Aprem Musique
            ("18:00", "20:00", FranceCulture), # Soft power
            ("20:00", "21:00", FranceInter), # soirée, masque et la plume
            ("21:00", "00:00", FranceInfo),
        ]
    },
)

music = Channel("musique", handlers=(AdsHandler,),
                timetable={(0, 1, 2, 3,): [
                    ("00:00", "09:00", RTL2),
                    ("09:00", "12:00", PycolorePlaylistStation),
                    ("12:00", "22:00", RTL2),
                    ("22:00", "00:00", PycolorePlaylistStation),
                ],
                (4,): [
                    ("00:00", "09:00", RTL2),
                    ("09:00", "12:00", PycolorePlaylistStation),
                    ("12:00", "22:00", RTL2),
                    ("22:00", "01:00", PycolorePlaylistStation),
                ],
                (5,): [
                    ("00:00", "01:00", PycolorePlaylistStation),
                    ("01:00", "09:00", RTL2),
                    ("09:00", "12:00", PycolorePlaylistStation),
                    ("12:00", "22:00", RTL2),
                    ("22:00", "01:00", PycolorePlaylistStation),
                ],
                (6,): [
                    ("00:00", "01:00", PycolorePlaylistStation),
                    ("00:00", "09:00", RTL2),
                    ("09:00", "12:00", PycolorePlaylistStation),
                    ("12:00", "22:00", RTL2),
                    ("22:00", "00:00", PycolorePlaylistStation),
                ]})

