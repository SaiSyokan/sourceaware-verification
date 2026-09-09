"""Command-line interface for validation, retrieval, inference, and evaluation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .evidence import EvidenceStore, collect_image_evidence, collect_text_evidence
from .evaluation import evaluate_factor_predictions, evaluate_predictions
from .finetune import prepare_factor_dataset
from .io import dump_json, dump_jsonl, load_jsonl
from .labels import decisions_from_label
from .llava_backend import LlavaBackend
from .manifest import validate_manifest
from .pipeline import PRIMARY_STRATEGY, STRATEGIES, SourceAwareVerifier
from .routing import InputAnalyzer, VerificationRouter


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sourceaware")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("manifest")
    validate.add_argument("--check-files", action="store_true")
    validate.add_argument("--media-root")
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("predictions")
    evaluate.add_argument("--output")
    evaluate_factors = sub.add_parser("evaluate-factors")
    evaluate_factors.add_argument("predictions")
    evaluate_factors.add_argument("--output")
    prepare = sub.add_parser("prepare-finetune")
    prepare.add_argument("--manifest", required=True)
    prepare.add_argument("--output", required=True)
    text = sub.add_parser("collect-text-evidence")
    text.add_argument("--manifest", required=True)
    text.add_argument("--output", required=True)
    text.add_argument("--limit", type=int, default=3)
    image = sub.add_parser("collect-image-evidence")
    image.add_argument("--manifest", required=True)
    image.add_argument("--output", required=True)
    image.add_argument("--limit", type=int, default=3)
    image.add_argument("--media-root")
    image.add_argument("--no-page-context", action="store_true")
    run = sub.add_parser("run")
    run.add_argument("--manifest", required=True)
    run.add_argument("--evidence-root", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--model-path", required=True)
    run.add_argument("--model-base")
    run.add_argument("--conversation-mode")
    run.add_argument("--media-root")
    run.add_argument("--strategy", choices=STRATEGIES, default=PRIMARY_STRATEGY)
    run.add_argument("--retrieval-limit", type=int, default=3)
    run.add_argument("--no-evidence", action="store_true")
    run.add_argument("--no-image-description", action="store_true")
    run.add_argument("--temperature", type=float, default=0.0)
    run.add_argument("--top-p", type=float)
    run.add_argument("--num-beams", type=int, default=1)
    run.add_argument("--max-new-tokens", type=int, default=512)
    run.add_argument("--seed", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.command == "validate":
        result = validate_manifest(args.manifest, args.check_files, args.media_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result["valid"]:
            raise SystemExit(1)
    elif args.command == "evaluate":
        print(json.dumps(evaluate_predictions(args.predictions, args.output), indent=2))
    elif args.command == "evaluate-factors":
        print(json.dumps(evaluate_factor_predictions(args.predictions, args.output), indent=2))
    elif args.command == "prepare-finetune":
        count = prepare_factor_dataset(args.manifest, args.output)
        print(json.dumps({"factor_instances": count, "output": args.output}))
    elif args.command == "collect-text-evidence":
        count = collect_text_evidence(args.manifest, args.output, args.limit)
        print(json.dumps({"collected": count, "kind": "text"}))
    elif args.command == "collect-image-evidence":
        count = collect_image_evidence(
            args.manifest,
            args.output,
            args.limit,
            args.media_root,
            not args.no_page_context,
        )
        print(json.dumps({"collected": count, "kind": "image"}))
    elif args.command == "run":
        backend = LlavaBackend(
            args.model_path,
            model_base=args.model_base,
            conversation_mode=args.conversation_mode,
            temperature=args.temperature,
            top_p=args.top_p,
            num_beams=args.num_beams,
            max_new_tokens=args.max_new_tokens,
            seed=args.seed,
        )
        verifier = SourceAwareVerifier(
            backend,
            EvidenceStore(args.evidence_root),
            use_evidence=not args.no_evidence,
            use_image_description=not args.no_image_description,
            retrieval_limit=args.retrieval_limit,
        )
        manifest_path = Path(args.manifest).expanduser().resolve()
        media_root = Path(args.media_root).resolve() if args.media_root else manifest_path.parent
        output_rows = []
        for row in load_jsonl(manifest_path):
            active_factors = {
                factor.id
                for factor in VerificationRouter().route(InputAnalyzer().analyze(row))
            }
            try:
                prediction = verifier.predict(row, media_root, args.strategy).to_dict()
            except Exception as exc:
                prediction = {
                    "sample_id": row.get("sample_id"),
                    "prediction": None,
                    "error": str(exc),
                }
            prediction["prediction"] = prediction.get("label")
            if "label" in row:
                prediction["gold_label"] = row["label"]
                all_gold = decisions_from_label(str(row["label"]))
                prediction["gold_decisions"] = {
                    key: value for key, value in all_gold.items() if key in active_factors
                }
            else:
                named_gold = {
                    "veracity:image": row.get("image_veracity"),
                    "veracity:text": row.get("text_veracity"),
                    "consistency:image:text": row.get("image_text_consistency"),
                }
                prediction["gold_decisions"] = {
                    key: str(value).upper()
                    for key, value in named_gold.items()
                    if value is not None
                }
            output_rows.append(prediction)
        dump_jsonl(args.output, output_rows)
        metadata = {
            "package_version": __version__,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "manifest": str(manifest_path),
            "strategy": args.strategy,
            "use_evidence": not args.no_evidence,
            "use_image_description": not args.no_image_description,
            "retrieval_limit": args.retrieval_limit,
            "model_path": args.model_path,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "num_beams": args.num_beams,
            "max_new_tokens": args.max_new_tokens,
            "seed": args.seed,
            "processed": len(output_rows),
        }
        dump_json(str(args.output) + ".run.json", metadata)
        print(json.dumps({"processed": len(output_rows), "output": args.output}))


if __name__ == "__main__":
    main()
