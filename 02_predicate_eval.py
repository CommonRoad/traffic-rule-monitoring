from pathlib import Path

import crmonitor
import crcpp


def execute_dateset_eval(config_path: Path):
    """
    Execute the dataset evaluation for all scenarios in the CommonRoad dataset.
    """
    monitor = crmonitor.Monitor(str(config_path))
    monitor.evaluate()

if __name__ == "__main__":
    execute_dateset_eval(Path(__file__).parent / "configurations/predicates/monitor.yaml")

    crcpp.SlowOtherVehiclePredicate.
