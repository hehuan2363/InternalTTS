from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, Optional, Tuple

import soundfile as sf
import torch
from huggingface_hub import hf_hub_download
from kokoro import KModel, KPipeline

REPO_ID = "hexgrad/Kokoro-82M"
DEFAULT_VOICE = "af_heart"


def sanitize_user_id(user_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", user_id or "default")


class TTSEngine:
    def __init__(
        self,
        model_dir: Path | str = Path("model"),
        audio_root: Path | str = Path("audio"),
        repo_id: str = REPO_ID,
        default_voice: str = DEFAULT_VOICE,
    ) -> None:
        self.model_dir = Path(model_dir)
        self.audio_root = Path(audio_root)
        self.repo_id = repo_id
        self.default_voice = default_voice

        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.audio_root.mkdir(parents=True, exist_ok=True)

        self._model: Optional[KModel] = None
        self._pipelines: Dict[str, KPipeline] = {}
        self._lock = Lock()

    def ensure_model_assets(self, voice: str) -> Tuple[Path, Path, Path]:
        voice = voice or self.default_voice
        assets = {
            "config.json": self.model_dir / "config.json",
            "kokoro-v1_0.pth": self.model_dir / "kokoro-v1_0.pth",
            f"voices/{voice}.pt": self.model_dir / "voices" / f"{voice}.pt",
        }

        for remote_name, local_path in assets.items():
            if local_path.exists():
                continue

            local_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Downloading {remote_name} to {local_path}")
            downloaded_path = hf_hub_download(
                repo_id=self.repo_id,
                filename=remote_name,
                local_dir=str(self.model_dir),
                local_dir_use_symlinks=False,
            )
            assets[remote_name] = Path(downloaded_path)

        return (
            assets["config.json"],
            assets["kokoro-v1_0.pth"],
            assets[f"voices/{voice}.pt"],
        )

    def _get_model(self, config_path: Path, weights_path: Path) -> KModel:
        if self._model is None:
            self._model = KModel(
                repo_id=self.repo_id,
                config=config_path,
                model=weights_path,
            )
        return self._model

    def _get_pipeline(self, voice: str) -> Tuple[KPipeline, Path]:
        voice = voice or self.default_voice

        with self._lock:
            config_path, weights_path, voice_path = self.ensure_model_assets(voice)
            model = self._get_model(config_path, weights_path)

            pipeline = self._pipelines.get(voice)
            if pipeline is None:
                pipeline = KPipeline(
                    lang_code="a",
                    repo_id=self.repo_id,
                    model=model,
                )
                self._pipelines[voice] = pipeline

        return pipeline, voice_path

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        user_id: str = "default",
    ) -> Path:
        voice = voice or self.default_voice
        text = text.strip()
        if not text:
            raise ValueError("Text must not be empty.")

        pipeline, voice_path = self._get_pipeline(voice)

        audio_chunks = []
        sample_rate = 24000
        generator = pipeline(text, voice=str(voice_path))
        for _, _, audio in generator:
            audio_chunks.append(audio)

        if not audio_chunks:
            raise RuntimeError("No audio produced by pipeline.")

        combined_audio = torch.cat(audio_chunks, dim=0)

        safe_user = sanitize_user_id(user_id)
        user_audio_dir = self.audio_root / safe_user
        user_audio_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{safe_user}_{voice}_{timestamp}.wav"
        output_path = user_audio_dir / output_filename

        sf.write(output_path, combined_audio.numpy(), sample_rate)
        return output_path
