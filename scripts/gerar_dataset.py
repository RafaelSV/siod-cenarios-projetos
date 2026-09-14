"""Converte as simulações MATLAB em um dataset NumPy do projeto agregado."""

from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path

import numpy as np


LOGGER = logging.getLogger("pipeline")
SPLIT_SEED = 42
PARAMETER_NAMES = (
    "Expected_Rew",
    "Expected_WU",
    "PCronograma",
    "PGestor",
    "Variacao_Capacidade_Base_Pct",
)
TASK_METADATA_NAMES = (
    "task_id",
    "expected_ini_tu",
    "expected_end_tu",
    "expected_duration",
    "expected_wu",
    "expected_workrate",
)
SERIES_NAMES = (
    "SimTime", "CapacidadeEquipe", "in_Perc_WRew", "in_Perc_WU",
    "in_Perc_WPCron", "in_Perc_WPGestor", "WTD", "WD", "WRew", "WU",
    "WPCron", "WPGestor", "RWTD", "RWD", "RWRew", "RWU", "RWPCron",
    "RWPGestor", "DeltaWTD", "DeltaWD", "DeltaWRew", "DeltaWU",
    "DeltaWPCron", "DeltaWPGestor", "DeltaRWTD", "DeltaRWD",
    "DeltaRWRew", "DeltaRWU", "DeltaRWPCron", "DeltaRWPGestor", "Enable",
    "EnableEfetivo", "Done", "ProjectTimeRemaining", "TaskTimeRemaining",
    "TaskStartDelay", "TaskDelay", "Wip", "TotalWork", "WRemaining",
    "PercAccomplished", "ProdutRequerida", "ProdutEsperada", "Perc_WRew",
    "Perc_WU", "Perc_WPCron", "Perc_WPGestor", "RequiredWRate",
    "FractionComplete", "FractionReported", "Da", "FTA", "TWA",
)
OUTPUT_NAMES = (
    "WTD", "WD", "WRew", "WU", "WPCron", "WPGestor", "WRemaining",
    "PercAccomplished", "ProdutRequerida", "ProdutEsperada", "RequiredWRate",
    "FractionComplete", "FractionReported", "TaskDelay",
    "ProjectTimeRemaining", "TaskTimeRemaining", "Da", "FTA", "TWA",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _text(value: object) -> str:
    array = np.asarray(value)
    if array.dtype == object and array.size == 1:
        return _text(array.item())
    if array.dtype.kind == "S":
        return "".join(item.decode("utf-8") for item in array.reshape(-1, order="F"))
    if array.dtype.kind == "U":
        return "".join(str(item) for item in array.reshape(-1, order="F"))
    raise ValueError("Texto MATLAB em formato inesperado.")


def _scalar(value: object, description: str) -> float:
    array = np.asarray(value)
    require(array.size == 1 and np.issubdtype(array.dtype, np.number),
            f"{description} deve ser numérico e escalar.")
    return float(array.reshape(-1)[0])


def _struct_record(value: object, description: str) -> np.void:
    array = np.asarray(value)
    require(array.size == 1 and array.dtype.names is not None,
            f"{description} não é uma estrutura MATLAB válida.")
    return array.reshape(-1, order="F")[0]


def _table_columns(value: object, description: str) -> tuple[list[str], dict[str, object], int]:
    require(isinstance(value, dict), f"{description} não é uma tabela MATLAB válida.")
    required = {"data", "varnames", "nrows", "nvars"}
    require(required.issubset(value), f"{description} não contém a estrutura esperada.")
    names = [_text(item) for item in np.asarray(value["varnames"], dtype=object).reshape(-1, order="F")]
    data = list(np.asarray(value["data"], dtype=object).reshape(-1, order="F"))
    nrows = int(_scalar(value["nrows"], f"Número de linhas de {description}"))
    nvars = int(_scalar(value["nvars"], f"Número de variáveis de {description}"))
    require(nvars == len(names) == len(data), f"{description} possui colunas inconsistentes.")
    require(len(names) == len(set(names)), f"{description} possui nomes de coluna repetidos.")
    return names, dict(zip(names, data, strict=True)), nrows


def _numeric_columns(
    value: object,
    required_names: tuple[str, ...],
    description: str,
    expected_rows: int | None = None,
) -> np.ndarray:
    _, columns, nrows = _table_columns(value, description)
    missing = [name for name in required_names if name not in columns]
    require(not missing, f"{description} não contém: {', '.join(missing)}.")
    if expected_rows is not None:
        require(nrows == expected_rows,
                f"{description} possui {nrows} linhas; eram esperadas {expected_rows}.")
    selected: list[np.ndarray] = []
    for name in required_names:
        column = np.asarray(columns[name])
        require(np.issubdtype(column.dtype, np.number),
                f"A coluna {name} de {description} não é numérica.")
        column = column.reshape(-1, order="F")
        require(len(column) == nrows, f"A coluna {name} de {description} possui tamanho inválido.")
        selected.append(column.astype(np.float32, copy=False))
    matrix = np.column_stack(selected).astype(np.float32, copy=False)
    require(np.isfinite(matrix).all(), f"{description} contém NaN ou infinito.")
    return matrix


def deterministic_split(n_simulations: int) -> dict[str, np.ndarray]:
    """Reproduz o randperm usado pelo gerador anterior, com semente fixa 42."""
    require(n_simulations >= 7, "São necessárias pelo menos sete simulações.")
    random_values = np.random.RandomState(SPLIT_SEED).random_sample(n_simulations)
    order = np.argsort(random_values, kind="stable")
    n_train = int(np.floor(0.70 * n_simulations))
    n_validation = int(np.floor(0.15 * n_simulations))
    return {
        "train": order[:n_train].astype(np.int64),
        "validation": order[n_train:n_train + n_validation].astype(np.int64),
        "test": order[n_train + n_validation:].astype(np.int64),
    }


def _load_simulation(path: Path) -> tuple[np.ndarray, np.ndarray, int]:
    try:
        from matio import load_from_mat
    except ModuleNotFoundError as error:
        if error.name == "matio":
            raise ModuleNotFoundError(
                "Dependência mat-io ausente. Crie a .venv e execute "
                "'.venv\\Scripts\\python -m pip install -r requirements.txt'."
            ) from error
        raise

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="mat_to_table: MATLAB table version 5 is not supported.*")
        loaded = load_from_mat(path, variable_names=["P", "parametros"], raw_data=False)
    require("P" in loaded and "parametros" in loaded,
            f"{path.name} não contém P e parametros.")

    parameters = _numeric_columns(
        loaded["parametros"], PARAMETER_NAMES, f"parametros de {path.name}", expected_rows=1
    )[0]
    project_data = _struct_record(loaded["P"], f"P de {path.name}")
    project = _struct_record(project_data["Project"], f"P.Project de {path.name}")
    n_tasks = int(_scalar(project["nTasks"], f"P.Project.nTasks de {path.name}"))
    require(n_tasks > 0, f"{path.name} não possui tarefas.")
    _numeric_columns(
        project["Tasks"], TASK_METADATA_NAMES, f"P.Project.Tasks de {path.name}", expected_rows=n_tasks
    )

    runtime = np.asarray(project_data["Runtime"])
    require(runtime.dtype.names is not None and "SimData" in runtime.dtype.names,
            f"P.Runtime de {path.name} é inválido.")
    runtime_records = runtime.reshape(-1, order="F")
    require(len(runtime_records) == n_tasks + 1,
            f"P.Runtime de {path.name} deve conter as tarefas e o projeto agregado.")

    expected_rows: int | None = None
    for task_index, record in enumerate(runtime_records[:-1], start=1):
        task_series = _numeric_columns(
            record["SimData"], SERIES_NAMES, f"SimData da tarefa {task_index} de {path.name}", expected_rows
        )
        expected_rows = len(task_series)
    project_series = _numeric_columns(
        runtime_records[-1]["SimData"], SERIES_NAMES, f"SimData do projeto de {path.name}", expected_rows
    )
    return parameters, project_series, n_tasks


def _completion_summary(project_series: np.ndarray) -> dict[str, np.ndarray]:
    percentage = project_series[:, :, SERIES_NAMES.index("PercAccomplished")]
    simulation_time = project_series[:, :, SERIES_NAMES.index("SimTime")]
    reached_samples = percentage >= 100.0
    reached = reached_samples.any(axis=1)
    first_index = reached_samples.argmax(axis=1)
    time_reached = np.where(
        reached,
        simulation_time[np.arange(len(simulation_time)), first_index],
        np.nan,
    ).astype(np.float32)
    percent_missing = np.where(
        reached,
        0.0,
        np.maximum(0.0, 100.0 - percentage[:, -1]),
    ).astype(np.float32)
    return {
        "Atingiu100NoSimTime": reached.astype(np.uint8),
        "PercentualFaltantePara100": percent_missing,
        "TempoConclusaoProjeto": time_reached,
    }


def generate_project_dataset(
    simulations_dir: Path,
    output_dir: Path,
    max_simulations: int | None = None,
) -> tuple[Path, Path]:
    simulations_dir = simulations_dir.resolve()
    output_dir = output_dir.resolve()
    require(simulations_dir.is_dir(), f"Diretório de simulações não encontrado: {simulations_dir}")
    files = sorted(path for path in simulations_dir.glob("*.mat") if path.is_file())
    require(len(files) >= 7, "São necessárias pelo menos sete simulações .mat.")
    if max_simulations is not None:
        require(max_simulations >= 7, "--max-simulations deve ser pelo menos 7.")
        files = files[:max_simulations]
    require(len(files) >= 7, "O limite informado deixou menos de sete simulações.")
    LOGGER.info("Simulações localizadas: %d; simulações que serão consumidas: %d.",
                len(list(simulations_dir.glob("*.mat"))), len(files))

    parameter_rows: list[np.ndarray] = []
    project_rows: list[np.ndarray] = []
    n_tasks: int | None = None
    n_timesteps: int | None = None
    progress_interval = max(1, min(100, len(files) // 10))
    for index, path in enumerate(files, start=1):
        parameters, project_series, current_tasks = _load_simulation(path)
        if n_tasks is None:
            n_tasks = current_tasks
            n_timesteps = len(project_series)
            LOGGER.info("Estrutura identificada: %d tarefas, %d instantes e %d séries.",
                        n_tasks, n_timesteps, len(SERIES_NAMES))
        require(current_tasks == n_tasks, f"{path.name} possui quantidade diferente de tarefas.")
        require(len(project_series) == n_timesteps,
                f"{path.name} possui quantidade diferente de instantes.")
        parameter_rows.append(parameters)
        project_rows.append(project_series)
        if index % progress_interval == 0 or index == len(files):
            LOGGER.info("Leitura das simulações: %d/%d.", index, len(files))

    parameters = np.stack(parameter_rows).astype(np.float32, copy=False)
    project_series = np.stack(project_rows).astype(np.float32, copy=False)
    split = deterministic_split(len(files))
    LOGGER.info("Split fixo reproduzível: %d treino, %d validação e %d teste.",
                len(split["train"]), len(split["validation"]), len(split["test"]))

    project_inputs = np.empty(
        (len(files), int(n_timesteps), len(PARAMETER_NAMES) + 1), dtype=np.float32
    )
    project_inputs[:, :, :len(PARAMETER_NAMES)] = parameters[:, None, :]
    project_inputs[:, :, -1] = project_series[:, :, SERIES_NAMES.index("SimTime")]
    output_indices = [SERIES_NAMES.index(name) for name in OUTPUT_NAMES]
    completion = _completion_summary(project_series)

    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = output_dir / "dataset_projeto.npz"
    metadata_path = output_dir / "metadata.json"
    np.savez_compressed(
        dataset_path,
        X=project_inputs,
        Y=project_series[:, :, output_indices],
        **completion,
    )
    metadata = {
        "source": "Arquivos .mat do diretório informado à pipeline.",
        "n_simulations": len(files),
        "n_tasks": int(n_tasks),
        "n_timesteps": int(n_timesteps),
        "input_names": {"projeto": [*PARAMETER_NAMES, "SimTime"]},
        "output_names": list(OUTPUT_NAMES),
        "completion_summary": {
            "scope": "projeto",
            "threshold_percent": 100.0,
            "time_definition": "Primeiro SimTime amostrado com PercAccomplished >= 100.",
            "incomplete_time_value": "NaN.",
        },
        "split": {name: indices.tolist() for name, indices in split.items()},
        "split_seed": SPLIT_SEED,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    LOGGER.info("Dataset intermediário gravado em %s.", output_dir)
    return dataset_path, metadata_path
