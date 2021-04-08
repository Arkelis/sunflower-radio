
# API data that will be used in tests
from datetime import datetime

import pytest
from sunflower.core.custom_types import Broadcast
from sunflower.core.custom_types import BroadcastType
from sunflower.core.custom_types import SongPayload
from sunflower.core.custom_types import Step
from sunflower.stations import FranceInfo
from sunflower.stations import FranceInter
from sunflower.stations import FranceInterParis
from sunflower.utils import music

API_DATA = {
    "data": {
        "grid": [
            {
                "start": 1602738000,
                "end": 1602745200,
                "diffusion": {
                    "url": "https://www.franceinter.fr/emissions/le-7-9/le-7-9-15-octobre-2020",
                    "title": "Gaël Perdriau - Aurélien Rousseau",
                    "standFirst": "Gaël Perdriau, maire LR de Saint-Etienne, et Aurélien Rousseau, directeur général de l'Agence régional de santéd'Île-de-France, sont les invités du 7/9 de France Inter. ",
                    "show": {
                        "url": "https://www.franceinter.fr/emissions/le-7-9",
                        "title": "Le 7/9",
                        "podcast": {
                            "itunes": "https://podcasts.apple.com/fr/podcast/le-sept-neuf/id206501796",
                            "rss": "http://radiofrance-podcast.net/podcast09/rss_10241.xml"
                        }
                    }
                },
                "children": [
                    {
                        "start": 1602744870,
                        "end": 1602745050,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/le-billet-de-tanguy-pastureau/le-billet-de-tanguy-pastureau-15-octobre-2020",
                            "title": "Retour à l'enfance : Macron m'a puni de sortie",
                            "standFirst": "Ce matin, Tanguy revient sur les annonces d'Emmanuel Macron d'hier soir... ",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/le-billet-de-tanguy-pastureau",
                                "title": "Le billet de Tanguy Pastureau",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/le-billet-de-tanguy-pastureau/id1478436942",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_18644.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602744720,
                        "end": 1602744870,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/l-edito-m/l-edito-m-15-octobre-2020",
                            "title": "Facebook : le grand ménage d'automne ",
                            "standFirst": "A l’approche des élections américaines, Facebook multiplie les interdictions publicitaires sur ses réseaux.  ",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/l-edito-m",
                                "title": "L'édito M",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/ledito-m/id1365600334",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_18798.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602744360,
                        "end": 1602744720,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/la-revue-de-presse/la-revue-de-presse-15-octobre-2020",
                            "title": "La haine ne désarme pas contre Mila,17 ans, qui pense qu'elle mourra \"butée par un islamiste\". Le Point",
                            "standFirst": "Libération raconte Sainte-Livrade-sur-Lot, où en 1956 des vietnamiens rescapés de l’Indochine française construisirent une paix qui dure encore. Dans Paris Match, la dernière odyssée du motard Johnny Hallyday. La Voix du Nord me raconte Paulette, autrefois miséreuse, qui aide les pauvres en militant à  ATD Quart Monde.",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/la-revue-de-presse",
                                "title": "La Revue de presse",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/la-revue-de-presse/id115147880",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_18780.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602742900,
                        "end": 1602744230,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/l-invite-de-8h20-le-grand-entretien/l-invite-de-8h20-le-grand-entretien-15-octobre-2020",
                            "title": "Île-de-France : \"La situation s’est subitement dégradée\" d'après le directeur de l'ARS, Aurélien Rousseau",
                            "standFirst": "Alors que le président de la République a annoncé mercredi un couvre-feu pour Paris, l'Île-de-France et huit agglomérations, Aurélien Rousseau, directeur général de l'Agence régional de santé d'Île-de-France, est l'invité du Grand entretien de France Inter.",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/l-invite",
                                "title": "L'invité de 8h20 : le grand entretien",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/linvit%C3%A9-de-8h20-le-grand-entretien/id202987372",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_10239.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602742620,
                        "end": 1602742800,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/geopolitique/geopolitique-15-octobre-2020",
                            "title": "L’Europe parle d’une seule voix pour sanctionner Moscou sur l’affaire Navalny ",
                            "standFirst": "Moscou est furieux après la décision des « 27 » d’imposer des sanctions à l’entourage de Vladimir Poutine pour la tentative d’assassinat de l’opposant Alexei Navalny.",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/geopolitique",
                                "title": "Géopolitique",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/g%C3%A9opolitique/id115156820",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_10009.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602741600,
                        "end": 1602742560,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/le-journal-de-8h/le-journal-de-8h-15-octobre-2020",
                            "title": "Le journal de 8h du jeudi 15 octobre 2020",
                            "standFirst": None,
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/le-journal-de-8h",
                                "title": "Le journal de 8h",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/journal-de-08h00/id541446017",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_12495.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602741400,
                        "end": 1602741535,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/le-billet-de-charline-vanhoenacker/le-billet-de-charline-vanhoenacker-15-octobre-2020",
                            "title": "Couvre-feu : on va vivre comme des amish ! ",
                            "standFirst": "Elle était devant sa télé hier à 20 heures, et ce matin elle réagit aux annonces du président de la République… On accueille Catherine…",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/le-billet-de-charline-vanhoenacker",
                                "title": "Le Billet de Charline Vanhœnacker",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/le-billet-de-charline/id694238094",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_13129.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602740920,
                        "end": 1602741400,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/l-invite-de-7h50/l-invite-de-7h50-15-octobre-2020",
                            "title": "Couvre-feu : \"C’est un aveu de faiblesse\", juge le maire de Saint-Étienne Gaël Perdriau ",
                            "standFirst": "Gaël Perdriau, maire LR de Saint-Étienne, président de la métropole stéphanoise, réagit à l'annonce de l'entrée en vigueur d'un couvre-feu, samedi, dans neuf métropoles, dont Saint-Étienne, Paris et la région Île-de-France. ",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/invite-de-7h50",
                                "title": "L'invité de 7h50",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/linvit%C3%A9-de-7h50/id413088869",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_11710.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602740750,
                        "end": 1602740920,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/l-edito-eco/l-edito-eco-15-octobre-2020",
                            "title": "3 questions sur le couvre-feu",
                            "standFirst": "La décision de mettre en oeuvre le couvre-feu se comprend sur le plan sanitaire : il s'agit de réduire les interactions sociales. Mais sa traduction concrète est aussi le résultat de compromis discutables.",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/l-edito-eco",
                                "title": "L'Édito éco",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/l%C3%A9dito-%C3%A9co/id115147336",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_18770.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602740620,
                        "end": 1602740750,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/l-edito-politique/l-edito-politique-15-octobre-2020",
                            "title": "Couvre-feu… Encore une épreuve pour la cohésion nationale",
                            "standFirst": "Emmanuel Macron, hier soir à la télévision, appelle à la cohésion nationale… ",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/l-edito-politique",
                                "title": "L'édito politique",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/l%C3%A9dito-politique/id306757988",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_10217.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602739800,
                        "end": 1602740520,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/le-journal-de-7h30/le-journal-de-7h30-15-octobre-2020",
                            "title": "Un couvre feu mais pas seulement",
                            "standFirst": "Derrière la principale mesure annoncée hier, le chef de l'Etat a dévoilé aussi une nouvelle stratégie sanitaire.Des tests plus rapides, une nouvelle application téléphonique, et des repas limités à 6 personnes\r\n",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/le-journal-de-7h30",
                                "title": "Le journal de 7h30",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/journal-de-07h30/id556627193",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_12632.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602739705,
                        "end": 1602739765,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/la-meteo/la-meteo-15-octobre-2020",
                            "title": "Météo du jeudi 15 octobre 2020",
                            "standFirst": ".",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/la-meteo",
                                "title": "La météo",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/la-m%C3%A9t%C3%A9o/id1442688327",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_19490.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602739375,
                        "end": 1602739615,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/le-mur-du-son/le-mur-du-son-15-octobre-2020",
                            "title": "Renaud, chanteur énervant !",
                            "standFirst": "Renaud la « Putain d’expo » ouvre demain au public au « Musée de la musique » comme il l’appelle.Renaud au Musée ? Lui qui chantait quoi déjà ? « Société tu m’auras pas »...",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/le-mur-du-son",
                                "title": "Le mur du son",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/le-mur-du-son/id1528996666?uo=4",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_21480.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602739230,
                        "end": 1602739375,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/l-edito-carre/l-edito-carre-15-octobre-2020",
                            "title": "Pourquoi le soleil brille ? ",
                            "standFirst": "Une question simple mais vertigineuse, qui a fait réfléchir des générations de scientifiques… Depuis des milliers d’années, les hommes se sont demandés pourquoi le soleil brille brille brille… (petit clin d’œil à Annie Cordy)  Quelle est donc la nature et l’origine du formidable éclat de notre étoile ?   ",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/l-edito-carre",
                                "title": "L'Édito carré",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/l%C3%A9dito-carr%C3%A9/id1275617862",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_18099.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602738960,
                        "end": 1602739230,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/le-zoom-de-la-redaction/le-zoom-de-la-redaction-15-octobre-2020",
                            "title": "Un an auprès des Alcooliques Anonymes",
                            "standFirst": "Le \"Zoom\" ce matin nous conduit dans un endroit où il est très rare de pouvoir poser un micro : dans une réunion des Alcooliques Anonymes qui font bientôt célébrer les 60 ans de présence en France. France Inter a pu suivre un groupe pendant près d'une année. Reportage.",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/le-zoom-de-la-redaction",
                                "title": "Le Zoom de la rédaction",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/le-zoom-de-la-r%C3%A9daction/id306758571",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_10265.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602738880,
                        "end": 1602738960,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/les-80-de/les-80-de-15-octobre-2020",
                            "title": "\"Bordel, cette américanisation !\"",
                            "standFirst": "Le thème, et l’anathème, de \"l’américanisation\" de la France sont anciens. Autrefois on parlait de \"coca-colonisation\" des modes de vie. ",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/les-80-de-nicolas-demorand",
                                "title": "Les 80\" de...",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/les-80-de/id1434322790",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_19573.xml"
                                }
                            }
                        }
                    },
                    {
                        "start": 1602738010,
                        # démarrer à 07 h 00 et 10 secondes pour avoir un trou avant le premier programme enfant
                        "end": 1602738780,
                        "diffusion": {
                            "url": "https://www.franceinter.fr/emissions/journal-de-7h/journal-de-7h-15-octobre-2020",
                            "title": "Retour au bercail à 21 heures pour 20 millions de français !",
                            "standFirst": "Le chef de l'Etat a annoncé hier soir l'instauration d'un couvre feu en Ile de France et dans 8 métropoles à partir de samedi et pour 6 semaines. Emmanuel Macron en appelle à la responsabilité de chacun pour lutter contre l'épidémie qui a fait plus de 33 000 morts. ",
                            "show": {
                                "url": "https://www.franceinter.fr/emissions/le-journal-de-7h",
                                "title": "Journal de 7h",
                                "podcast": {
                                    "itunes": "https://podcasts.apple.com/fr/podcast/journal-de-07h00/id541446023",
                                    "rss": "http://radiofrance-podcast.net/podcast09/rss_12494.xml"
                                }
                            }
                        }
                    }
                ]
            },
            { # piste musicale
                "start": 1610662504,
                "end": 1610662753,
                "track": {
                    "title": "Jamileh",
                    "albumTitle": "BBE Stafff selections 2020",
                    "mainArtists": [
                        "Ihsan Al-Munzer"
                    ],
                    "performers": [
                        "Ihsan Al-Munzer"
                    ]
                }
            },
            { # piste sans mainArtists
                "start": 1610307944,
                "end": 1610308075,
                "track": {
                  "title": "ENFANT LIVRE",
                  "albumTitle": "Remparts d'argile",
                  "mainArtists": [],
                  "performers": [
                    "HENRI TEXIER"
                  ]
                }
            },
            { # blank step franceinfo
                "start": 1610662290,
                "end": 1610662800,
                "title": "Les nouvelles mesures sanitaires pour les écoles"
            }
        ]
    }
}


@pytest.fixture
def monkeypatch_apple_podcast(monkeypatch):

    def mock_apple_podcast(podcast_link: str, fallback: str):
        if podcast_link == "https://podcasts.apple.com/fr/podcast/le-sept-neuf/id206501796":
            return "https://is3-ssl.mzstatic.com/image/thumb/Podcasts113/v4/88/31/cb/8831cb22-ff5f-03fa-7815-1c57552ea7d7/mza_5059723156060763498.jpg/626x0w.webp"
        elif podcast_link == "https://podcasts.apple.com/fr/podcast/journal-de-07h00/id541446023":
            return "https://is3-ssl.mzstatic.com/image/thumb/Podcasts113/v4/fc/74/e8/fc74e883-1a69-3b9d-70f4-43e185f57db6/mza_6895079223603784045.jpg/626x0w.webp"
        elif podcast_link == "https://podcasts.apple.com/fr/podcast/les-80-de/id1434322790":
            return "https://is3-ssl.mzstatic.com/image/thumb/Podcasts113/v4/9f/7c/81/9f7c81de-7d7d-6d54-27a2-c0e52509cb43/mza_3524174555840859685.jpg/626x0w.webp"

    monkeypatch.setattr(music, "fetch_apple_podcast_cover", mock_apple_podcast)


def test_basic_radiofrance_diffusion_step(monkeypatch_apple_podcast):
    """Test radiofrance'step parsing:

    Undetailed step without child precision.
    """
    parsed_step = FranceInter()._get_radiofrance_programme_step(
        api_data=API_DATA["data"]["grid"][0],
        dt=datetime.fromtimestamp(1602738000),
        child_precision=False,
        detailed=False)

    expected_step = Step(
        start=1602738000,
        end=1602745200,
        broadcast=Broadcast(title="Gaël Perdriau - Aurélien Rousseau",
                            type=BroadcastType.PROGRAMME,
                            station=FranceInter().station_info,
                            thumbnail_src="https://is3-ssl.mzstatic.com/image/thumb/Podcasts113/v4/88/31/cb/8831cb22-ff5f-03fa-7815-1c57552ea7d7/mza_5059723156060763498.jpg/626x0w.webp",
                            show_title="Le 7/9",))

    assert parsed_step == expected_step


def test_detailed_radiofrance_diffusion_step_without_child_precision(monkeypatch_apple_podcast):
    """Test radiofrance'step parsing:

    Detailed step without child precision.
    """
    parsed_step = FranceInter()._get_radiofrance_programme_step(
        api_data=API_DATA["data"]["grid"][0],
        dt=datetime.fromtimestamp(1602738000),
        child_precision=False,
        detailed=True)

    expected_step = Step(
        start=1602738000,
        end=1602745200,
        broadcast=Broadcast(title="Gaël Perdriau - Aurélien Rousseau",
                            summary="Gaël Perdriau, maire LR de Saint-Etienne, et Aurélien Rousseau, directeur général de l'Agence régional de santéd'Île-de-France, sont les invités du 7/9 de France Inter.",
                            type=BroadcastType.PROGRAMME,
                            station=FranceInter().station_info,
                            thumbnail_src="https://is3-ssl.mzstatic.com/image/thumb/Podcasts113/v4/88/31/cb/8831cb22-ff5f-03fa-7815-1c57552ea7d7/mza_5059723156060763498.jpg/626x0w.webp",
                            link='https://www.franceinter.fr/emissions/le-7-9/le-7-9-15-octobre-2020',
                            show_title="Le 7/9",
                            show_link="https://www.franceinter.fr/emissions/le-7-9"))

    assert parsed_step == expected_step


def test_detailed_radiofrance_diffusion_step_beore_first_child(monkeypatch_apple_podcast):
    """Test radiofrance'step parsing:

    Detailed step with child precision (before first child programme).
    """
    parsed_step = FranceInter()._get_radiofrance_programme_step(
        api_data=API_DATA["data"]["grid"][0],
        dt=datetime.fromtimestamp(1602738000),
        child_precision=True,
        detailed=True)

    expected_step = Step(
        start=1602738000,
        end=1602738010,
        broadcast=Broadcast(title="Gaël Perdriau - Aurélien Rousseau",
                            summary="Gaël Perdriau, maire LR de Saint-Etienne, et Aurélien Rousseau, directeur général de l'Agence régional de santéd'Île-de-France, sont les invités du 7/9 de France Inter.",
                            type=BroadcastType.PROGRAMME,
                            station=FranceInter().station_info,
                            thumbnail_src="https://is3-ssl.mzstatic.com/image/thumb/Podcasts113/v4/88/31/cb/8831cb22-ff5f-03fa-7815-1c57552ea7d7/mza_5059723156060763498.jpg/626x0w.webp",
                            link='https://www.franceinter.fr/emissions/le-7-9/le-7-9-15-octobre-2020',
                            show_title="Le 7/9",
                            show_link="https://www.franceinter.fr/emissions/le-7-9"))

    assert parsed_step == expected_step


def test_detailed_radiofrance_diffusion_step_first_child(monkeypatch_apple_podcast):
    """Test radiofrance'step parsing:

    Detailed step with child precision (first child programme).
    """
    parsed_step = FranceInter()._get_radiofrance_programme_step(
        api_data=API_DATA["data"]["grid"][0],
        dt=datetime.fromtimestamp(1602738010),
        child_precision=True,
        detailed=True)

    expected_step = Step(
        start=1602738010,
        end=1602738780,
        broadcast=Broadcast(title="Retour au bercail à 21 heures pour 20 millions de français !",
                            summary="Le chef de l'Etat a annoncé hier soir l'instauration d'un couvre feu en Ile de France et dans 8 métropoles à partir de samedi et pour 6 semaines. Emmanuel Macron en appelle à la responsabilité de chacun pour lutter contre l'épidémie qui a fait plus de 33 000 morts.",
                            type=BroadcastType.PROGRAMME,
                            station=FranceInter().station_info,
                            thumbnail_src="https://is3-ssl.mzstatic.com/image/thumb/Podcasts113/v4/fc/74/e8/fc74e883-1a69-3b9d-70f4-43e185f57db6/mza_6895079223603784045.jpg/626x0w.webp",
                            link="https://www.franceinter.fr/emissions/journal-de-7h/journal-de-7h-15-octobre-2020",
                            show_title="Journal de 7h",
                            show_link="https://www.franceinter.fr/emissions/le-journal-de-7h",
                            parent_show_title="Le 7/9",
                            parent_show_link="https://www.franceinter.fr/emissions/le-7-9"))

    assert parsed_step == expected_step


def test_detailed_radiofrance_diffusion_step_between_first_and_second_child(monkeypatch_apple_podcast):
    """Test radiofrance'step parsing:

    Detailed step with child precision (between two first children).
    """
    parsed_step = FranceInter()._get_radiofrance_programme_step(
        api_data=API_DATA["data"]["grid"][0],
        dt=datetime.fromtimestamp(1602738780),
        child_precision=True,
        detailed=True)

    expected_step = Step(
        start=1602738780,
        end=1602738880,
        broadcast=Broadcast(title="Gaël Perdriau - Aurélien Rousseau",
                            summary="Gaël Perdriau, maire LR de Saint-Etienne, et Aurélien Rousseau, directeur général de l'Agence régional de santéd'Île-de-France, sont les invités du 7/9 de France Inter.",
                            type=BroadcastType.PROGRAMME,
                            station=FranceInter().station_info,
                            thumbnail_src="https://is3-ssl.mzstatic.com/image/thumb/Podcasts113/v4/88/31/cb/8831cb22-ff5f-03fa-7815-1c57552ea7d7/mza_5059723156060763498.jpg/626x0w.webp",
                            link='https://www.franceinter.fr/emissions/le-7-9/le-7-9-15-octobre-2020',
                            show_title="Le 7/9",
                            show_link="https://www.franceinter.fr/emissions/le-7-9"))

    assert parsed_step == expected_step


def test_detailed_radiofrance_diffusion_step_second_child(monkeypatch_apple_podcast):
    """Test radiofrance'step parsing:

    Detailed step with child precision (second).
    """
    parsed_step = FranceInter()._get_radiofrance_programme_step(
        api_data=API_DATA["data"]["grid"][0],
        dt=datetime.fromtimestamp(1602738880),
        child_precision=True,
        detailed=True)

    expected_step = Step(
        start=1602738880,
        end=1602738960,
        broadcast=Broadcast(title="\"Bordel, cette américanisation !\"",
                            summary="Le thème, et l’anathème, de \"l’américanisation\" de la France sont anciens. Autrefois on parlait de \"coca-colonisation\" des modes de vie.",
                            type=BroadcastType.PROGRAMME,
                            station=FranceInter().station_info,
                            thumbnail_src="https://is3-ssl.mzstatic.com/image/thumb/Podcasts113/v4/9f/7c/81/9f7c81de-7d7d-6d54-27a2-c0e52509cb43/mza_3524174555840859685.jpg/626x0w.webp",
                            link="https://www.franceinter.fr/emissions/les-80-de/les-80-de-15-octobre-2020",
                            show_title="Les 80\" de...",
                            show_link="https://www.franceinter.fr/emissions/les-80-de-nicolas-demorand",
                            parent_show_title="Le 7/9",
                            parent_show_link="https://www.franceinter.fr/emissions/le-7-9"))

    assert parsed_step == expected_step


def test_detailed_radiofrance_diffusion_step_after_last_child(monkeypatch_apple_podcast):
    """Test radiofrance'step parsing:

    Detailed step with child precision (after last child).
    """
    parsed_step = FranceInter()._get_radiofrance_programme_step(
        api_data=API_DATA["data"]["grid"][0],
        dt=datetime.fromtimestamp(1602745050),
        child_precision=True,
        detailed=True)

    expected_step = Step(
        start=1602745050,
        end=1602745200,
        broadcast=Broadcast(title="Gaël Perdriau - Aurélien Rousseau",
                            summary="Gaël Perdriau, maire LR de Saint-Etienne, et Aurélien Rousseau, directeur général de l'Agence régional de santéd'Île-de-France, sont les invités du 7/9 de France Inter.",
                            type=BroadcastType.PROGRAMME,
                            station=FranceInter().station_info,
                            thumbnail_src="https://is3-ssl.mzstatic.com/image/thumb/Podcasts113/v4/88/31/cb/8831cb22-ff5f-03fa-7815-1c57552ea7d7/mza_5059723156060763498.jpg/626x0w.webp",
                            link='https://www.franceinter.fr/emissions/le-7-9/le-7-9-15-octobre-2020',
                            show_title="Le 7/9",
                            show_link="https://www.franceinter.fr/emissions/le-7-9"))

    assert parsed_step == expected_step


def test_radiofrance_track_step():
    """Test radiofrance step parsing:

    Track step
    """
    parsed_step = FranceInterParis()._get_radiofrance_track_step(
        api_data=API_DATA["data"]["grid"][1],
        dt=datetime.fromtimestamp(1610662504))

    expected_step = Step(
        start=1610662504,
        end=1610662753,
        broadcast=Broadcast(
            title="Ihsan Al-Munzer • Jamileh",
            type=BroadcastType.MUSIC,
            station=FranceInterParis().station_info,
            thumbnail_src="https://cdns-images.dzcdn.net/images/artist/a1a23844fed57b71fd1f18a9f633636e/500x500-000000-80-0-0.jpg",
            summary=FranceInterParis.station_slogan,
            metadata=SongPayload(title='Jamileh', artist='Ihsan Al-Munzer', album=''),
            link="https://www.deezer.com/artist/65281352"))

    assert parsed_step == expected_step


def test_radiofrance_track_step_without_artist():
    """Test radiofrance step parsing:

    Track step without mainArtists field
    """
    parsed_step = FranceInterParis()._get_radiofrance_track_step(
        api_data=API_DATA["data"]["grid"][2],
        dt=datetime.fromtimestamp(1610307944))

    expected_step = Step(
        start=1610307944,
        end=1610308075,
        broadcast=Broadcast(
            title="HENRI TEXIER • ENFANT LIVRE",
            type=BroadcastType.MUSIC,
            station=FranceInterParis().station_info,
            thumbnail_src="https://cdns-images.dzcdn.net/images/artist/345f1b012b55d907be32e0b80864fed2/500x500-000000-80-0-0.jpg",
            summary=FranceInterParis.station_slogan,
            metadata=SongPayload(title='ENFANT LIVRE', artist='HENRI TEXIER', album=''),
            link="https://www.deezer.com/artist/153756"))

    assert parsed_step == expected_step


def test_radiofrance_blank_step():
    """Test radiofrance step parsing:

    Blank step
    """
    parsed_step = FranceInfo()._get_radiofrance_programme_step(
        api_data=API_DATA["data"]["grid"][3],
        dt=datetime.fromtimestamp(1610662290),
        child_precision=True,
        detailed=True)

    expected_step = Step(
        start=1610662290,
        end=1610662800,
        broadcast=Broadcast(
            title="Les nouvelles mesures sanitaires pour les écoles",
            type=BroadcastType.PROGRAMME,
            station=FranceInfo().station_info,
            thumbnail_src=FranceInfo.station_thumbnail))

    assert parsed_step == expected_step

