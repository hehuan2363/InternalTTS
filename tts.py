#!/usr/bin/env python3
"""
Kokoro TTS Local Script
A text-to-speech script using the Kokoro-82M model with streaming support.
"""

import argparse
import sys

from tts_engine import DEFAULT_VOICE, TTSEngine


def parse_args():
    parser = argparse.ArgumentParser(description="Generate speech using Kokoro locally.")
    parser.add_argument("text", nargs="?", help="Text to convert to speech.")
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"Voice to use (default: {DEFAULT_VOICE}).",
    )
    parser.add_argument(
        "--user",
        default="cli",
        help="Identifier used to group generated audio files.",
    )
    return parser.parse_args()


def get_text_input(arg_text: str | None) -> str:
    if arg_text:
        print(f"Using provided text: {arg_text[:50]}{'...' if len(arg_text) > 50 else ''}")
        return arg_text

    print("Enter text to convert to speech:")
    print("(Press Ctrl+D or Ctrl+C to exit)")
    try:
        text = input("> ").strip()
        if not text:
            print("No text provided. Exiting.")
            sys.exit(1)
        return text
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        sys.exit(0)


def main():
    print("Kokoro TTS Script")
    print("================")

    args = parse_args()

    text = get_text_input(args.text)
    engine = TTSEngine()

    try:
        output_path = engine.synthesize(
            text=text,
            voice=args.voice,
            user_id=args.user,
        )
    except Exception as exc:
        print(f"❌ Audio generation failed: {exc}")
        sys.exit(1)

    print(f"\n✅ Audio generation completed!")
    print(f"📁 Output file: {output_path.absolute()}")
    print(f"🎵 Sample rate: 24kHz")
    print(f"🎤 Voice: {args.voice}")


if __name__ == "__main__":
    main()
