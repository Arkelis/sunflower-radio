# This file is part of sunflower package. Radio app.

"""Module containing radio metadata fetching related functions."""

from sunflower.core.bases import Channel
from sunflower.handlers import AdsHandler
from sunflower.stations import FranceCulture
from sunflower.stations import FranceInfo
from sunflower.stations import FranceInter
from sunflower.stations import FranceInterParis
from sunflower.stations import FranceMusique
from sunflower.stations import PycolorePlaylistStation
from sunflower.stations import RTL2

tournesol = Channel(
    endpoint="tournesol",
    timetable={
        # (weekday1, weekday2, ...)
        (0, 1, 2, 3, 4): [
            # (start, end, station_name),
            ("00:00", "05:00", FranceCulture), # Les nuits de France Culture
            ("06:00", "10:00", FranceInter), # Matinale, Boomerang, l'instant M
            ("10:00", "12:00", FranceCulture), # Les chemins de la philosophie, Culture monde
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
            ("11:00", "12:00", FranceCulture), # Affaires étrangères
            ("12:00", "14:00", FranceInter), # Le grand face à face
            ("14:00", "17:00", FranceCulture), # Plan large, Toute une vie, La Conversation scientifique
            ("17:00", "18:00", FranceInter), # La preuve par Z
            ("18:00", "19:00", FranceCulture), # Débat
            ("19:00", "21:00", FranceInfo), # Les informés
            ("21:00", "00:00", FranceCulture), # Soirée Culture (Fiction, Mauvais Genre, rediff Toute une vie)
        ],
        (6,): [
            ("00:00", "07:00", FranceCulture), # Les nuits de France Culture
            ("07:00", "09:00", FranceMusique), # Bach
            ("09:00", "10:00", FranceInter), # Interception
            ("10:00", "11:00", FranceInfo),
            ("11:00", "14:00", FranceInter), # On va déguster, politique, journal
            ("14:00", "18:00", FranceMusique), # Aprem Musique
            ("18:00", "19:00", FranceInfo), # Le masque et la plume
            ("19:00", "22:00", FranceInter), # Le masque et la plume, Autant en emporte l'histoire
            ("22:00", "00:00", FranceInterParis),
        ]
    },
)

music = Channel("musique", handlers=(AdsHandler,),
                timetable={(0, 1, 2, 3,): [
                    ("00:00", "06:00", FranceInterParis),
                    ("06:00", "09:00", RTL2),
                    ("09:00", "12:00", PycolorePlaylistStation),
                    ("12:00", "13:30", RTL2),
                    ("13:30", "18:00", FranceInterParis),
                    ("18:00", "22:00", RTL2),
                    ("22:00", "00:00", PycolorePlaylistStation),
                ],
                (4,): [
                    ("00:00", "06:00", FranceInterParis),
                    ("06:00", "09:00", RTL2),
                    ("09:00", "12:00", PycolorePlaylistStation),
                    ("12:00", "13:30", RTL2),
                    ("13:30", "18:00", FranceInterParis),
                    ("18:00", "22:00", RTL2),
                    ("22:00", "01:00", PycolorePlaylistStation),
                ],
                (5,): [
                    ("00:00", "01:00", PycolorePlaylistStation),
                    ("01:00", "06:00", FranceInterParis),
                    ("06:00", "09:00", RTL2),
                    ("09:00", "12:00", PycolorePlaylistStation),
                    ("12:00", "13:30", RTL2),
                    ("13:30", "18:00", FranceInterParis),
                    ("18:00", "22:00", RTL2),
                    ("22:00", "01:00", PycolorePlaylistStation),
                ],
                (6,): [
                    ("00:00", "01:00", PycolorePlaylistStation),
                    ("01:00", "06:00", FranceInterParis),
                    ("06:00", "09:00", RTL2),
                    ("09:00", "12:00", PycolorePlaylistStation),
                    ("12:00", "13:30", RTL2),
                    ("13:30", "22:00", FranceInterParis),
                    ("22:00", "00:00", PycolorePlaylistStation),
                ]})

