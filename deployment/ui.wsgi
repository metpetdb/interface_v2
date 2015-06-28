import dotenv
from pathlib import Path

from app import metpet_ui as application


dotenv.read_dotenv(Path.cwd().joinpath('app_variables.env').as_posix())
activate_this = '~/.virtualenvs/ui/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
