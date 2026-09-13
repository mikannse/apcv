"""Back-compat shim: the full pipeline lives in apcv.cli.main."""
from apcv.cli.main import app

if __name__ == "__main__":
    app()
