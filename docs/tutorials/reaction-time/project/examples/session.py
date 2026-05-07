import datetime
import os
import git

from ucl_open.core.experiment import ExperimentSession

session = ExperimentSession(
    subject_id="Plimbo",
    session_id="001",
    workflow="main.bonsai",
    commit=git.Repo(search_parent_directories=True).head.object.hexsha,
    repository_url=""
)

def main(path_seed: str = "./local/{schema}.json"):
    os.makedirs(os.path.dirname(path_seed), exist_ok=True)
    models = [session]

    for model in models:
        with open(path_seed.format(schema=model.__class__.__name__), "w", encoding="utf-8") as f:
            f.write(model.model_dump_json(indent=2, by_alias=True))


if __name__ == "__main__":
    main()