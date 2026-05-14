import os

from ucl_open_reaction_time.task import (
    UclOpenReactionTimeTaskLogic,
    UclOpenReactionTimeTaskParameters,
    Trial
)

task_logic = UclOpenReactionTimeTaskLogic(
    task_parameters=UclOpenReactionTimeTaskParameters(
        max_trial_time=60,
        initial_delay_time=5,
        trials=[
            Trial(temporal_frequency=1, target_delay=1),
            Trial(temporal_frequency=2, target_delay=2),
            Trial(temporal_frequency=1, target_delay=1),
            Trial(temporal_frequency=2, target_delay=2),
            Trial(temporal_frequency=1, target_delay=1)
        ]
    ),
)

def main(path_seed: str = "./local/{schema}.json"):
    example_task_logic = task_logic
    os.makedirs(os.path.dirname(path_seed), exist_ok=True)
    models = [example_task_logic]

    for model in models:
        with open(path_seed.format(schema=model.__class__.__name__), "w", encoding="utf-8") as f:
            f.write(model.model_dump_json(indent=2, by_alias=True))


if __name__ == "__main__":
    main()