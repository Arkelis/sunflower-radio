# This is Sunflower Radio app.

"""Module containing radio metadata fetching related functions."""

from sunflower.core.bases import Channel
from sunflower.handlers import AdsHandler
from sunflower.stations import (RTL2, FranceCulture, FranceInfo, FranceInter,
                                FranceMusique, PycolorePlaylistStation)

tournesol = Channel(
    endpoint="tournesol",
    handlers=(AdsHandler,),
    timetable={
        # (weekday1, weekday2, ...)
        (0, 1, 2, 3, 4): [
            # (start, end, station_name),
            ("00:00", "05:00", FranceCulture), # Les nuits de France Culture
            ("05:00", "07:00", FranceInfo), # Matinale
            ("07:00", "09:00", FranceInter), # Matinale
            ("09:00", "11:00", PycolorePlaylistStation), # Musique
            ("11:00", "12:00", FranceCulture), # Toute une vie
            ("12:00", "15:00", FranceInter), # Jeu des mille, journal, boomerang
            ("15:00", "18:00", FranceCulture), # La compagnie des auteurs/poètes, La Méthode scientifique, LSD (la série docu)
            ("18:00", "20:00", FranceInter), # Soirée
            ("20:00", "21:00", FranceInfo), # Les informés
            ("21:00", "22:00", RTL2), # Musique
            ("22:00", "00:00", PycolorePlaylistStation), # Musique
        ],
        (5,): [
            ("00:00", "06:00", FranceCulture), # Les nuits de France Culture
            ("06:00", "07:00", FranceInfo), # Matinale
            ("06:00", "09:00", FranceInter), # Matinale
            ("09:00", "11:00", PycolorePlaylistStation), # Musique
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
            ("09:00", "12:00", PycolorePlaylistStation),
            ("12:00", "14:00", FranceInter), # Politique + journal
            ("14:00", "18:00", FranceMusique), # Aprem Musique : Carrefour de Lodéon et La tribune des critiques de disques
            # ("18:00", "19:00", RTL2),
            ("18:00", "21:00", FranceInter), # Spécial Corona : téléphone sonne et le masque et la plume
            ("21:00", "22:00", RTL2),
            ("22:00", "00:00", PycolorePlaylistStation),
        ]
    },
)

music = Channel("music", handlers=(AdsHandler,),
                timetable={(0, 1, 2, 3, 4, 5, 6,): [
                    ("00:00", "09:00", RTL2),
                    ("09:00", "12:00", PycolorePlaylistStation),
                    ("11:00", "22:00", RTL2),
                    ("22:00", "00:00", PycolorePlaylistStation),
                ]})
