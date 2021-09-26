# IntraRez

Application Flask de l'Intranet de la Rez.

## Exigences

* Python : Probablement >= 3.10 à terme, pour l'instant >= 3.8 suffit ;
* Autres packages Linux : ``mysql-server postfix git``, plus pour le
  déploiement : ``supervisor nginx`` ;
* Packages Python : Voir [`requirements.txt`](requirements.txt), plus pour le
  déploiement : ``gunicorn pymysql cryptography`` ;
* Pour le déploiement : un utilisateur Linux ``intrarez`` dédié.



## Installation

Je reprends pour l'essentiel le déploiement conseillé dans le tutoriel :
https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvii-deployment-on-linux

* Installer l'application :

  ```
  cd /home/intrarez
  git clone https://github.com/GRI-ESPCI/intrarez
  cd intrarez
  python3 -m venv env
  source env/bin/activate
  pip install -r requirements.txt
  pip install gunicorn pymysql cryptography
  cp .conf_models/model.env .env
  ```

* Créer et initialiser la base de données MySQL :

  ```
  sudo mysql -u root
  ```
  ```sql
  CREATE DATABASE intrarez CHARACTER SET utf8 COLLATE utf8_bin;
  CREATE USER 'intrarez'@'localhost' IDENTIFIED BY '<mdp-db>';
  GRANT ALL PRIVILEGES ON intrarez.* TO 'intrarez'@'localhost';
  FLUSH PRIVILEGES;
  QUIT;
  ```
  ```
  flask db upgrade
  ```

* Modifier le fichier ``.env`` créé depuis le modèle.
  Pour générer une ``SECRET_KEY`` aléatoire :

  ```
  python3 -c "import uuid; print(uuid.uuid4().hex)"
  ```

* Enregistrer l'application dans les variables d'environment :

  ```
  echo "export FLASK_APP=intrarez.py" >> ~/.profile
  ```

* Compiler les traductions (fichiers binaires) :

  ```
  flask translate compile
  ```

* Installer les dépendances bower

  ```
  bower install
  ```

L'application peut alors normalement être lancée avec ``flask run``.

On a alors une version de développement installée : ``flask run`` n'est pas
approprié à de la production (peu optimisé), et il faut configurer l'accès
depuis l'extérieur (même si c'est un extérieur interne, dans notre cas).


### Passage en production

On utilise Gunicorn en interne : le serveur Python n'est pas accessible de
l'extérieur, c'est Nginx qui lui servira les requêtes non-statiques.

Gunicorn est lancé et contrôlé par Supervisor, qui fait à peu près le travail
d'un service mais en plus pratique :

```
sudo cp .conf_models/supervisor.conf /etc/supervisor/conf.d/intrarez.conf
sudo supervisorctl reload
```

Le nombre de *workers* de Gunicorn (le ``-w 4`` dans le fichier de conf)
peut être adapté selon la machine.

Configuration de Nginx :

```
sudo cp .conf_models/nginx.conf /etc/nginx/sites-enabled/intrarez
sudo service nginx reload
```

**Note : pour l'instant, l'application est configurée pour ne fonctionner
qu'en HTTP, pas en HTTPS (problèmes de certificats en réseau interne).**

Il faudra tester et voir ce qui marche mieux en terme d'avertissements des
navigateurs et autres entre ça et un certificat auto-host : voir
[`.conf_models/nginx.conf`](.conf_models/nginx.conf), avec

```
mkdir certs
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
  -keyout certs/key.pem -out certs/cert.pem
```

Compliqué d'avoir un vrai certificat, parce qu'il faut un nom de domaine
associé, mais si on veut mettre des services accessibles depuis l'extérieur
ce sera une étape obligée.


### Mise à jour

Pour mettre à jour l'application, dans le dossier ``intrarez`` :

```bash
git pull
source env/bin/activate
supervisorctl stop intrarez
flask db upgrade
flask translate compile
sudo supervisorctl start intrarez
```

(côté développement, voir plus bas)



## Notes de développement

Je vais ici noter pas à pas ce que je fais, pour simplifier au maximum
l'appréhension du code par d'éventuels GRI futurs.


### Début de l'installation

### 11/09/2021 - Loïc 137

Tout a été créé en suivant ce tutoriel :
https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

Requirements : je pars sur Python 3.10, parce que le nouveau statement `match`
me fait beaucoup trop de l'oeil.

À ce jour, Python 3.10 n'est disponible qu'en version *release candidate* 2
(donc quasiment finale), et devrait sortir début octobre (donc avant la
release de l'IntraRez).

Installation propre de plusieurs versions de Python sur un même OS :
https://hackersandslackers.com/multiple-python-versions-ubuntu-20-04

Installation d'un virtual env fresh

Utilisation de SQLAlchemy 1.4 (2.x pas prêt)

Gestion des migrations de db : lors du développement d'une nouvelle version
modifiant le modèle de données,
* En local : ``flask db migrate -m "Migration to <version>"`` ;
* Vérifier le fichier créé dans ``migrations/versions`` ;
* ``flask db upgrade`` pour appliquer localement ;
* (autres modifs hors db)
* Release de la version ;
* En prod : pull puis ``flask db upgrade``.


Je pars sur une structure en modules (basée sur les *blueprints* Flask),
détaillée au chapitre XV du tuto :
https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xv-a-better-application-structure


Application bilingue (utilisant Flask-Babel) : lorsque le code est modifié,
* Exécuter ``flask translate update`` ;
* Modifier/ajouter les clés de traduction dans
  ``app/translations/en/LC_MESSAGES/messages.po``. Les entrées modifiées
  sont indiquées avec ``#, fuzzy`` : **supprimer ce commentaire** après
  avoir vérifié qu'il n'y avait pas d'erreur / modifié la traduction ;
* Exécuter ``flask translate compile``.


### 20/09/21 - Loïc 137

Abandon de Flask-Bootstrap, qui est sur Bootstrap 3 et assez restreignant.

À la place, je crée le template de base à la main (en créant à peu près
les blocs que Flask-Bootstrap créait), de même pour le template des forms.

J'ai repris le code de Flask-Bootstrap pour ce qui est de la gestion des
forms, directement dans [`app/templates/_form.html`](app/templates/_form.html).

Utilisation des icônes SVG [Bootstrap Icons](https://icons.getbootstrap.com/),
directement dans app/static/svg. Voir le code d'affichage des notifications
dans [`app/templates/base.php`](app/templates/base.php) pour savoir comment
utiliser ces icônes (rechercher `svg`).
