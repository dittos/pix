import argparse
import importlib

import tqdm

from pix.app import create_graph
from pixdb.repo import Repo
from pixdb.schema import Indexer


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True, dest="command")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("task")

    rebuild_index_parser = subparsers.add_parser("rebuild-index")
    rebuild_index_parser.add_argument("repo")
    rebuild_index_parser.add_argument("index")

    args = parser.parse_args()

    if args.command == "run":
        func = getattr(importlib.import_module("pix.task." + args.task), "main")
        
        graph = create_graph()
        graph.run(func)
    elif args.command == "rebuild-index":
        repo_module, repo_attr = args.repo.split(":")
        repo_cls = getattr(importlib.import_module(repo_module), repo_attr)
        graph = create_graph()
        repo: Repo = graph.get_instance(repo_cls)
        indexer = getattr(repo, args.index)
        if not isinstance(indexer, Indexer):
            raise ValueError(f"{args.repo} {args.index} is not an Indexer")
        
        with tqdm.tqdm() as progress:
            repo.rebuild_index([indexer], progress_callback=progress.update)
    else:
        raise ValueError(args.command)


if __name__ == "__main__":
    main()
