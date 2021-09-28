"""Intranet de la Rez Flask App - custom CLI commands"""

import os
import subprocess
from shutil import which

import click
from app.tools.utils import printProgressBar


def register(app):
    @app.cli.group()
    def translate():
        """Translation and localization commands."""
        pass

    @translate.command()
    @click.argument("lang")
    def init(lang):
        """Initialize a new language."""
        if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
            raise RuntimeError("extract command failed")
        if os.system(
            f"pybabel init -i messages.pot -d app/translations -l {lang}"
        ):
            raise RuntimeError("init command failed")
        os.remove("messages.pot")

    @translate.command()
    def update():
        """Update all languages."""
        if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
            raise RuntimeError("extract command failed")
        if os.system("pybabel update -i messages.pot -d app/translations"):
            raise RuntimeError("update command failed")
        os.remove("messages.pot")

    @translate.command()
    def compile():
        """Compile all languages."""
        if os.system("pybabel compile -d app/translations"):
            raise RuntimeError("compile command failed")

    @app.cli.group()
    def sass():
        """Gestion des scripts sass et scss"""
        pass

    @sass.command()
    def compile():
        """
        Compilation des scripts scss file en css
        Les fichiers dans app/static/src/scss/*.scss
        sont compilés dans app/static/css/compiled/*.css.
        """

        if which("sass") is None:
            print("La commande sass n'est pas installée. Imposssible de compiler le scss.")
            return -1

        scss_files = [a for a in os.listdir("app/static/src/scss/") if a.endswith('.scss')]
        length = len(scss_files)

        print("Compilation des fichiers scss")
        printProgressBar(0, length, prefix='Progression :', length=50)
        for i, file in enumerate(scss_files):
            filename = os.path.splitext(file)[0]
            scss_path = os.path.join(
                'app/static/src/scss/',
                f'{filename}.scss'
            )
            css_path = os.path.join(
                'app/static/css/compiled/',
                f"{filename}.css"
            )
            process = subprocess.run(
                ['sass', scss_path, css_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            printProgressBar(i + 1, length, prefix='Progression :', length=50)

            if process.returncode != 0:
                print(f"Erreur lors de la compilation de {scss_path}.\n")
