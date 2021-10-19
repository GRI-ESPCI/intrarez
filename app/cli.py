"""Intranet de la Rez Flask App - custom CLI commands"""

import os
import subprocess
from shutil import which

import click
from app.tools.utils import print_progressbar, run_script


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
        """Commandes de gestion des scripts SASS et SCSS."""
        pass

    @sass.command()
    def compile():
        """Compilation des scripts SCSS en CSS.

        Les fichiers SCSS dans app/static/scss sont
        compilés dans app/static/css/compiled/*.css.
        """
        if which("sass") is None:
            print("La commande 'sass' n'est pas installée. "
                  "Impossible de compiler le SCSS.")
            return -1

        source_folder = "app/static/scss/"
        compiled_folder = "app/static/css/compiled/"
        if not os.path.exists(compiled_folder):
            os.mkdir(compiled_folder)

        scss_files = [a for a in os.listdir(source_folder)
                      if a.endswith(".scss")]
        length = len(scss_files)

        print("Compilation des fichiers SCSS")
        print_progressbar(0, length, prefix="Progression :", length=50)
        for i, file in enumerate(scss_files):
            filename = os.path.splitext(file)[0]
            scss_path = os.path.join(source_folder, f"{filename}.scss")
            css_path = os.path.join(compiled_folder, f"{filename}.css")
            result = subprocess.run(["sass", "--trace", scss_path, css_path],
                                    capture_output=True)

            print_progressbar(i + 1, length, prefix="Progression :", length=50)

            if result.returncode != 0:
                print(f"Erreur lors de la compilation de '{scss_path}' :")
                print(f"\033[91m{result.stderr.decode()}\033[0m")


    @app.cli.command()
    @click.argument("name")
    def script(name):
        """Run the script <NAME> in the application context."""
        run_script(name)
