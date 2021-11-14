# Scripts IntraRez

Les fichiers `.py` dans ce dossier sont des scripts exécutables dans le
contexte applicatif de l'IntraRez.

Pour exécuter le script `<name>.py` :

```py
cd /home/intrarez/intrarez
source env/bin/activate
flask script <name>
```

Les scripts doivent comporter une fonction `main()`, qui sera appelée
(sans arguments) par `flask script`.
