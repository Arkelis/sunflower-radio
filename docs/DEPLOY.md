# Déploiement de Radio Tournesol

Cette page détaille les étapes pour déployer Radio Tournesol sur un serveur
Debian 10 Buster.

## Installation du planificateur des chaînes

### Redis

Le planificateur utilise Redis pour persister des données.

```zsh
sudo apt install redis
```

### Pyenv

Nous allons utiliser [pyenv](https://github.com/pyenv/pyenv) pour installer
Python sur le serveur.

```zsh
# installation des prérequis
sudo apt update
sudo apt install git make build-essential libssl-dev zlib1g-dev libbz2-dev \
     libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils \
     tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# installation de pyenv
git clone https://github.com/pyenv/pyenv.git ~/.pyenv

# si nécessaire, ajout d'export de variables à .zshenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshenv
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshenv

# si nécessaire, ajout de pyenv init dans .zshrc
echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.zshrc

# redémarrer le shell pour bénéficier des changements
exec "$SHELL"

# installation de Python 3.8.8
pyenv install 3.8.8
```

### Pyenv

On peut maintenant installer Poetry.

```zsh
# on passe sur Python 3.8.8
pyenv global 3.8.8

# on vérifie la version de Python
python --version

# si ce n'est pas la bonne, redémarrer le shell
# installation de poetry
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
```

### Installation du projet

On installe le projet dans `/var/www/api.radio.pycolore.fr`

```zsh
sudo mkdir -p /var/www/api.radio.pycolore.fr
sudo chown -R guillaume:guillaume /var/www/api.radio.pycolore.fr
cd /var/www/api.radio.pycolore.fr
git clone --branch master git@github.com:Arkelis/sunflower-radio.git .
poetry install
```

## Installation de Liquidsoap

### Opam

Opam est le gestionnaire de dépendances OCaml, il va nous permettre à la fois
d'installer OCaml et Liquidsoap.

```zsh
# installation
sh <(curl -sL https://raw.githubusercontent.com/ocaml/opam/master/shell/install.sh)

# si nécessaire, ajouter au .zshrc
echo 'test -r $HOME/.opam/opam-init/init.zsh && . $HOME/.opam/opam-init/init.zsh > /dev/null 2> /dev/null || true' >> ~/.zshrc
```

### Liquidsoap

Opam installe automatiquement un compilateur OCaml. On n'a plus qu'à installer
Liquidsoap

```zsh
opam depext taglib mad vorbis cry opus samplerate faad liquidsoap
opam install taglib mad vorbis cry opus samplerate faad liquidsoap
```

## Installation de Icecast

### Icecast

On commence par installer Icecast2. Lorsque demandé, indiquer comme 
nom de domaine `icecast.pycolore.fr`.

```zsh
sudo apt install icecast2
```

Il est nécessaire d'éditer le fichier de configuration de Icecast.

```zsh
sudo vim /etc/icecast2/icecast.xml
```

En dessous de la balise `<hostname>`, modifier le premier `<listen-socket>`
(touche `A` pour entrer en mode insertion) :

```xml
<listen-socket>
    <port>3333</port>
    <bind-address>127.0.0.1</bind-address> 
    <ssl>0</ssl>
</listen-socket>
```

Sauvegarder et quitter Vim : `Echap` puis `ZZ`.

On va faire écouter Icecast sur le port 3333 uniquement en localhost. C'est 
Nginx qui va rediriger le trafic entrant vers ce socket.

### Proxy web

Nous allons utiliser nginx devant Icecast. En effet, le but est de rendre
Icecast accessible à l'adresse `https://icecast.pycolore.fr` sur le port
HTTPS classique, soit 443. Or si Icecast écoute directement ce port, aucun
autre site ne pourra être servi sur ce port. On utiliser donc Nginx qui
s'occupe ensuite de rediriger où il faut les requêtes entrantes.

```zsh
# installation de certbot (ssl) et nginx
sudo apt install nginx python3-certbot-nginx

# configuration du proxy
echo "upstream icecast {
    server localhost:3333;
}

server {
    server_name icecast.pycolore.fr;
    listen [::]:80;
    listen 80;
    return 301 https://icecast.pycolore.fr$request_uri;
}

server {
    server_name icecast.pycolore.fr;
    listen [::]:443;
    listen 443;
    
    location / {
        include proxy_params;
        proxy_buffering off;
        proxy_pass http://icecast;
    }
}" | sudo tee /etc/nginx/sites-available/icecast.pycolore.fr

# activation du site
sudo ln -s /etc/nginx/sites-enabled/icecast.pycolore.fr \
           /etc/nginx/sites-available/icecast.pycolore.fr

# création du certificat
# sélection le bon domaine quand demandé
sudo certbot --nginx

# rechargement de nginx
sudo systemctl reload nginx
```


## Lancement

Il faut s'assurer que le dossier `~/radio` est bien complet avec :

- `songs` : dossier contenant les fichier audio de la playlist Pycolore
- `franceinfo-long.ogg` : audio de transition

On commence par générer la config Liquidsoap :

```zsh
cd /var/www/api.radio.pycolore.fr
poetry run python sunflower/write_config.py
mv sunflower.liq ~/radio/sunflower.liq
```

On est parés pour lancer :

```zsh
cd /var/www/api.radio.pycolore.fr
poetry run make start-liquidsoap
poetry run make start-scheduler
```
