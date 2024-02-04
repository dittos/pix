import argparse
import importlib

from pix.app import create_graph


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True, dest="command")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("task")

    args = parser.parse_args()

    func = getattr(importlib.import_module("pix.task." + args.task), "main")
    
    graph = create_graph()
    graph.run(func)


if __name__ == "__main__":
    main()
