"""Prepara dados de simulação para treinamento de uma ESN."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from gerar_dataset import SPLIT_SEED, deterministic_split, generate_project_dataset


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = ROOT / "data" / "simulacoes_100"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "processed"
DEFAULT_GENERATED_DIR = ROOT / "data" / "generated"
TARGET = "PercAccomplished"
INPUT_FIELDS = [
    "Expected_Rew",
    "Expected_WU",
    "PCronograma",
    "PGestor",
    "Variacao_Capacidade_Base_Pct",
    "SimTime",
]
SCENARIO_FIELDS = INPUT_FIELDS[:-1]
LOGGER = logging.getLogger("pipeline")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
        stream=sys.stdout,
    )


def load_metadata(path: Path) -> dict:
    require(
        path.is_file(),
        f"Metadado obrigatório não encontrado ao lado do NPZ: {path}",
    )
    metadata = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(metadata, dict), "O metadado deve ser um objeto JSON.")
    return metadata


def validate_dataset(dataset_path: Path, metadata_path: Path) -> tuple[dict, dict]:
    LOGGER.info("Lendo metadados e validando o esquema do dataset.")
    require(dataset_path.is_file(), f"Dataset não encontrado: {dataset_path}")
    metadata = load_metadata(metadata_path)
    input_names = metadata.get("input_names", {}).get("projeto")
    output_names = metadata.get("output_names")
    require(isinstance(input_names, list), "Lista input_names.projeto ausente no metadado.")
    require(isinstance(output_names, list), "Lista output_names ausente no metadado.")
    require(len(input_names) == len(set(input_names)), "Há nomes de entrada duplicados.")
    require(len(output_names) == len(set(output_names)), "Há nomes de saída duplicados.")
    require(input_names == INPUT_FIELDS, f"Entradas esperadas: {INPUT_FIELDS}; recebidas: {input_names}.")
    require(TARGET in output_names, f"Alvo obrigatório ausente: {TARGET}.")

    LOGGER.info("Carregando os tensores X e Y.")
    with np.load(dataset_path, allow_pickle=False) as archive:
        require("X" in archive.files and "Y" in archive.files, "O NPZ deve conter X e Y.")
        arrays = {name: archive[name].copy() for name in archive.files}
    x = arrays["X"].astype(np.float32, copy=False)
    y_all = arrays["Y"].astype(np.float32, copy=False)
    require(x.ndim == 3 and y_all.ndim == 3, "X e Y devem ter três dimensões.")
    require(x.shape[:2] == y_all.shape[:2], "X e Y diferem nos eixos cenário/tempo.")
    require(x.shape[2] == len(input_names), "Quantidade de entradas difere do metadado.")
    require(y_all.shape[2] == len(output_names), "Quantidade de saídas difere do metadado.")
    n_scenarios, n_times = x.shape[:2]
    if metadata.get("n_simulations") is not None:
        require(n_scenarios == int(metadata["n_simulations"]), "Número de cenários difere do metadado.")
    if metadata.get("n_timesteps") is not None:
        require(n_times == int(metadata["n_timesteps"]), "Número de instantes difere do metadado.")

    if "simulation_id" in arrays:
        ids = arrays["simulation_id"]
        id_rule = "IDs lidos do vetor simulation_id do NPZ."
    else:
        ids = np.arange(n_scenarios, dtype=np.int64)
        id_rule = "IDs definidos pela posição do cenário no NPZ, de 0 a N-1."
    require(ids.ndim == 1 and len(ids) == n_scenarios, "Vetor simulation_id incompatível.")
    require(np.issubdtype(ids.dtype, np.integer), "simulation_id deve ser inteiro.")
    require(len(np.unique(ids)) == n_scenarios, "Há simulation_id duplicado.")

    y = y_all[:, :, [output_names.index(TARGET)]]
    require(np.isfinite(x).all(), "Há NaN ou infinito em X.")
    require(np.isfinite(y).all(), "Há NaN ou infinito no alvo.")
    require(np.allclose(x[:, :, :5], x[:, :1, :5]), "Parâmetros variam dentro do cenário.")
    sim_time = x[:, :, INPUT_FIELDS.index("SimTime")]
    require(np.all(np.diff(sim_time, axis=1) > 0), "SimTime não é estritamente crescente.")
    require(np.allclose(sim_time, sim_time[:1]), "Os cenários possuem grades temporais diferentes.")
    require(
        n_times == 61 and np.allclose(sim_time[0], np.arange(61, dtype=np.float32)),
        "A grade esperada de SimTime é de 0 a 60, com 61 instantes.",
    )
    for name in INPUT_FIELDS[:4]:
        values = x[:, :, INPUT_FIELDS.index(name)]
        require(np.logical_and(values >= 0, values <= 30).all(), f"{name} fora de [0, 30].")
    capacity = x[:, :, INPUT_FIELDS.index("Variacao_Capacidade_Base_Pct")]
    require(np.logical_and(capacity >= -20, capacity <= 30).all(),
            "Variacao_Capacidade_Base_Pct fora de [-20, 30].")
    progress = y[:, :, 0]
    require(np.logical_and(progress >= -1e-6, progress <= 100 + 1e-6).all(),
            "PercAccomplished fora de [0, 100].")
    require((np.diff(progress, axis=1) >= -1e-6).all(), "PercAccomplished diminui em algum cenário.")
    LOGGER.info("Dataset validado: %d cenários, %d instantes e alvo %s.", n_scenarios, n_times, TARGET)
    return metadata, {"X": x, "Y": y, "simulation_id": ids.astype(np.int64), "id_rule": id_rule}


def create_split(metadata: dict, n_scenarios: int) -> tuple[dict[str, np.ndarray], str]:
    source_split = metadata.get("split")
    if isinstance(source_split, dict) and all(name in source_split for name in ("train", "validation", "test")):
        split = {name: np.asarray(source_split[name], dtype=np.int64) for name in ("train", "validation", "test")}
        source = "Divisão existente no metadado de origem."
    else:
        split = deterministic_split(n_scenarios)
        source = f"Divisão criada por cenário: 70%/15%/15%, regra fixa {SPLIT_SEED}."
    combined = np.concatenate(list(split.values()))
    require(len(combined) == n_scenarios, "A divisão não cobre todos os cenários.")
    require(len(np.unique(combined)) == n_scenarios, "Há sobreposição entre treino, validação e teste.")
    require(set(combined.tolist()) == set(range(n_scenarios)), "A divisão possui índices inválidos.")
    require(all(len(indices) > 0 for indices in split.values()), "Algum conjunto da divisão ficou vazio.")
    LOGGER.info(
        "Divisão por cenário validada: %d treino, %d validação e %d teste.",
        len(split["train"]), len(split["validation"]), len(split["test"]),
    )
    return split, source


def normalization(values: np.ndarray, train_indices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    train = values[train_indices]
    mean = train.mean(axis=(0, 1), dtype=np.float64).astype(np.float32)
    std = train.std(axis=(0, 1), dtype=np.float64).astype(np.float32)
    std[~np.isfinite(std) | (std < 1e-12)] = 1.0
    return mean, std


def prepare_outputs(dataset_path: Path, metadata_path: Path, output_dir: Path) -> dict:
    pd.options.future.infer_string = False
    metadata, data = validate_dataset(dataset_path, metadata_path)
    x, y, ids = data["X"], data["Y"], data["simulation_id"]
    split, split_rule = create_split(metadata, len(x))

    LOGGER.info("Calculando a normalização exclusivamente com o conjunto de treino.")
    input_mean, input_std = normalization(x, split["train"])
    target_mean, target_std = normalization(y, split["train"])
    x_normalized = ((x - input_mean) / input_std).astype(np.float32)
    y_normalized = ((y - target_mean) / target_std).astype(np.float32)
    require(np.isfinite(x_normalized).all() and np.isfinite(y_normalized).all(),
            "A normalização produziu valores inválidos.")

    progress = y[:, :, 0]
    time = x[:, :, INPUT_FIELDS.index("SimTime")]
    reached_samples = progress >= 100
    reached = reached_samples.any(axis=1)
    first_index = reached_samples.argmax(axis=1)
    completion_time = np.where(
        reached,
        time[np.arange(len(time)), first_index],
        np.nan,
    ).astype(np.float32)
    deficit = np.where(reached, 0, np.maximum(0, 100 - progress[:, -1])).astype(np.float32)
    set_name = np.empty(len(x), dtype=object)
    for name, indices in split.items():
        set_name[indices] = {"train": "treino", "validation": "validacao", "test": "teste"}[name]

    LOGGER.info("Montando dataset normalizado e resumo por cenário.")
    summary_data: dict[str, np.ndarray] = {"simulation_id": ids}
    for index, name in enumerate(SCENARIO_FIELDS):
        summary_data[name] = x[:, 0, index]
    summary_data.update({
        "conjunto": set_name,
        "progresso_final_pct": progress[:, -1],
        "concluiu_ate_60": reached.astype(np.uint8),
        "tempo_conclusao_tu": completion_time,
        "deficit_final_pp": deficit,
    })
    summary = pd.DataFrame(summary_data).sort_values("simulation_id")
    require(not summary.simulation_id.duplicated().any(), "O resumo contém IDs duplicados.")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pipeline-esn-", dir=output_dir.parent) as temporary_name:
        temporary = Path(temporary_name)
        dataset_output = temporary / "dataset_esn.npz"
        metadata_output = temporary / "metadata_esn.json"
        summary_output = temporary / "resumo_cenarios.csv"
        np.savez_compressed(
            dataset_output,
            X=x_normalized,
            Y=y_normalized,
            simulation_id=ids,
            train_indices=split["train"],
            validation_indices=split["validation"],
            test_indices=split["test"],
        )
        prepared_metadata = {
            "purpose": "Entrada normalizada para treinamento da ESN de progresso do projeto.",
            "input_names": INPUT_FIELDS,
            "target_names": [TARGET],
            "tensor_layout": "cenario, instante, variavel",
            "dtype": "float32",
            "normalized": True,
            "n_simulations": int(len(x)),
            "n_timesteps": int(x.shape[1]),
            "input_shape": list(x_normalized.shape),
            "target_shape": list(y_normalized.shape),
            "split": {
                "rule": split_rule,
                "train": int(len(split["train"])),
                "validation": int(len(split["validation"])),
                "test": int(len(split["test"])),
            },
            "normalization": {
                "rule": "Média e desvio calculados somente com os cenários de treino.",
                "input_mean": input_mean.tolist(),
                "input_std": input_std.tolist(),
                "target_mean": target_mean.tolist(),
                "target_std": target_std.tolist(),
                "inverse_target": "Y_original = Y_normalizado * target_std + target_mean",
            },
            "simulation_id_rule": data["id_rule"],
            "completion": {
                "threshold_percent": 100.0,
                "horizon_tu": float(time[0, -1]),
                "time_definition": "Primeiro SimTime com PercAccomplished >= 100.",
            },
        }
        metadata_output.write_text(
            json.dumps(prepared_metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        summary.to_csv(
            summary_output,
            index=False,
            encoding="utf-8",
            lineterminator="\r\n",
            float_format="%.9g",
            na_rep="",
        )
        LOGGER.info("Validando as três saídas antes da publicação local.")
        with np.load(dataset_output, allow_pickle=False) as check:
            require(check["X"].shape == x_normalized.shape, "Dimensão de X mudou na gravação.")
            require(check["Y"].shape == y_normalized.shape, "Dimensão de Y mudou na gravação.")
            require(np.isfinite(check["X"]).all() and np.isfinite(check["Y"]).all(),
                    "O dataset gravado contém valor inválido.")
        check_metadata = load_metadata(metadata_output)
        require(check_metadata["input_shape"] == list(x_normalized.shape), "Metadado de saída inconsistente.")
        check_summary = pd.read_csv(summary_output)
        require(len(check_summary) == len(x), "Resumo gravado com quantidade incorreta.")

        output_dir.mkdir(parents=True, exist_ok=True)
        for source in (dataset_output, metadata_output, summary_output):
            source.replace(output_dir / source.name)

    return {
        "scenarios": int(len(x)),
        "timesteps": int(x.shape[1]),
        "train": int(len(split["train"])),
        "validation": int(len(split["validation"])),
        "test": int(len(split["test"])),
        "completed": int(reached.sum()),
        "not_completed": int((~reached).sum()),
        "discarded": 0,
        "corrected": 0,
        "warnings": 0,
        "output_dir": output_dir,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        nargs="?",
        choices=("dataset", "simulations", "generate-dataset"),
        default="dataset",
        help="Etapa em que a execução começa; o padrão é dataset.",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        help="Diretório do dataset ou das simulações, conforme o modo.",
    )
    parser.add_argument("--output-dir", type=Path, help="Diretório opcional das saídas.")
    parser.add_argument(
        "--max-simulations",
        type=int,
        help="Limita os .mat, principalmente para validar a pipeline.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging()
    LOGGER.info("Pipeline iniciada.")
    if args.max_simulations is not None and args.max_simulations < 7:
        LOGGER.error("--max-simulations deve ser pelo menos 7 para manter treino, validação e teste.")
        return 2
    if args.mode == "dataset" and args.max_simulations is not None:
        LOGGER.error("--max-simulations só se aplica aos modos simulations e generate-dataset.")
        return 2
    if args.mode != "dataset" and args.directory is None:
        LOGGER.error("O modo %s exige o diretório das simulações.", args.mode)
        return 2

    default_output = DEFAULT_GENERATED_DIR if args.mode == "generate-dataset" else DEFAULT_OUTPUT_DIR
    output_dir = (args.output_dir or default_output).resolve()

    try:
        if args.mode == "generate-dataset":
            simulations_dir = args.directory.resolve()
            LOGGER.info("Modo: gerar somente o dataset a partir das simulações.")
            generate_project_dataset(simulations_dir, output_dir, args.max_simulations)
            LOGGER.info("Pipeline concluída após a geração de dataset_projeto.npz e metadata.json.")
            return 0
        if args.mode == "simulations":
            simulations_dir = args.directory.resolve()
            LOGGER.info("Modo: fluxo completo a partir das simulações.")
            with tempfile.TemporaryDirectory(prefix="simulacoes-dataset-") as work_name:
                dataset, metadata = generate_project_dataset(
                    simulations_dir, Path(work_name), args.max_simulations
                )
                LOGGER.info("Dataset intermediário concluído; iniciando a preparação para a ESN.")
                report = prepare_outputs(dataset, metadata, output_dir)
        else:
            dataset_dir = (args.directory or DEFAULT_DATASET_DIR).resolve()
            dataset = dataset_dir / "dataset_projeto.npz"
            metadata = dataset_dir / "metadata.json"
            LOGGER.info("Modo: fluxo a partir do dataset já criado.")
            LOGGER.info("Diretório do dataset: %s.", dataset_dir)
            report = prepare_outputs(dataset, metadata, output_dir)
    except Exception as error:
        LOGGER.error("Pipeline interrompida: %s", error)
        return 1

    LOGGER.info("Saídas gravadas em %s.", report["output_dir"])
    LOGGER.info("dataset_esn.npz: %d cenários, %d instantes, alvo %s.",
                report["scenarios"], report["timesteps"], TARGET)
    LOGGER.info("Split: %d treino, %d validação e %d teste.",
                report["train"], report["validation"], report["test"])
    LOGGER.info("Resumo: %d concluídos e %d não concluídos até o horizonte.",
                report["completed"], report["not_completed"])
    LOGGER.info("Registros descartados: %d; correções: %d; alertas: %d.",
                report["discarded"], report["corrected"], report["warnings"])
    LOGGER.info("Pipeline concluída com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
