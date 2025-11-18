import argparse
from bcipydummies import EmotivController

def main():
    parser = argparse.ArgumentParser(description="Control BCI simple para videojuegos.")
    parser.add_argument("--window", required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--secret", required=True)

    args = parser.parse_args()

    ctrl = EmotivController(args.window, args.id, args.secret)
    ctrl.start()

if __name__ == "__main__":
    main()
