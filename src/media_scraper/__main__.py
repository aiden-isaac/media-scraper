from .cli import main as cli_main

import sys


def main():
    """Entry point: if 'gui' is first arg, start the web GUI."""
    args = list(sys.argv[1:])
    if args and args[0] == "gui":
        from .gui import app
        import uvicorn
        port = 8000
        host = "127.0.0.1"
        for i, a in enumerate(args):
            if a == "--port" and i + 1 < len(args):
                port = int(args[i + 1])
            elif a == "--host" and i + 1 < len(args):
                host = args[i + 1]
        print(f"[INFO] Media Scraper GUI running at http://{host}:{port}")
        print(f"[INFO] Open your browser to start researching")
        return uvicorn.run(app, host=host, port=port)
    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
