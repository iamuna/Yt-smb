from __future__ import annotations

import os
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from shorts_factory.config import ensure_directories, load_settings, save_settings
from shorts_factory.pipeline import BuildRequest, create_short
from shorts_factory.utils import executable_available

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ShortsFactoryApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ensure_directories()
        self.settings = load_settings()
        self.last_output: Path | None = None

        self.title("YT SMB — Shorts Factory")
        self.geometry("980x720")
        self.minsize(860, 620)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._refresh_engine_status()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="YT SMB  •  SHORTS FACTORY",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(18, 2))

        ctk.CTkLabel(
            header,
            text="Choose clips → add a hook/script → create a vertical Short.",
            text_color=("gray35", "gray70"),
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        self.engine_badge = ctk.CTkLabel(
            header, text="CHECKING...", corner_radius=12, padx=12, pady=6
        )
        self.engine_badge.grid(row=0, column=1, rowspan=2, padx=24)

    def _build_body(self) -> None:
        main = ctk.CTkScrollableFrame(self)
        main.grid(row=1, column=0, sticky="nsew", padx=18, pady=18)
        main.grid_columnconfigure(0, weight=1)

        self._section(main, 0, "1  Source clips")
        row = ctk.CTkFrame(main)
        row.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        row.grid_columnconfigure(0, weight=1)

        self.source_var = ctk.StringVar(value=self.settings["source_folder"])
        ctk.CTkEntry(row, textvariable=self.source_var, height=42).grid(
            row=0, column=0, sticky="ew", padx=(12, 8), pady=12
        )
        ctk.CTkButton(
            row, text="Choose folder", width=135, command=self._choose_source
        ).grid(row=0, column=1, padx=(0, 12), pady=12)

        self._section(main, 2, "2  Hook")
        self.hook_entry = ctk.CTkEntry(
            main,
            height=44,
            placeholder_text="Example: This sounds impossible, but it's real...",
        )
        self.hook_entry.grid(row=3, column=0, sticky="ew", pady=(0, 18))

        self._section(main, 4, "3  Narration / script")
        self.script_box = ctk.CTkTextbox(main, height=175)
        self.script_box.grid(row=5, column=0, sticky="ew", pady=(0, 14))

        options = ctk.CTkFrame(main)
        options.grid(row=6, column=0, sticky="ew", pady=(0, 18))
        options.grid_columnconfigure(0, weight=1)

        self.voice_enabled = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options, text="Generate AI voice-over", variable=self.voice_enabled
        ).grid(row=0, column=0, padx=14, pady=14, sticky="w")

        ctk.CTkLabel(options, text="Length").grid(
            row=0, column=1, padx=(12, 4), pady=14
        )
        self.length_var = ctk.StringVar(value=str(self.settings["target_seconds"]))
        ctk.CTkOptionMenu(
            options,
            variable=self.length_var,
            values=["15", "25", "35", "45", "60"],
            width=90,
        ).grid(row=0, column=2, padx=(4, 14), pady=14)

        self.create_button = ctk.CTkButton(
            main,
            text="CREATE SHORT",
            height=58,
            font=ctk.CTkFont(size=20, weight="bold"),
            command=self._start_build,
        )
        self.create_button.grid(row=7, column=0, sticky="ew", pady=(2, 12))

        self.progress = ctk.CTkProgressBar(main, mode="indeterminate")
        self.progress.grid(row=8, column=0, sticky="ew", pady=(0, 10))
        self.progress.stop()
        self.progress.set(0)

        self.result_label = ctk.CTkLabel(
            main, text="Ready.", anchor="w", justify="left", wraplength=800
        )
        self.result_label.grid(row=9, column=0, sticky="ew", pady=(0, 10))

        self.open_output_button = ctk.CTkButton(
            main,
            text="Open output folder",
            command=self._open_output,
            state="disabled",
        )
        self.open_output_button.grid(row=10, column=0, sticky="w", pady=(0, 14))

        note = ctk.CTkFrame(main)
        note.grid(row=11, column=0, sticky="ew", pady=(4, 8))
        ctk.CTkLabel(
            note,
            text=(
                "AUTO-PUBLISH: OFF  •  Publishing comes in the next checkpoint. "
                "Use footage you own or have permission to reuse."
            ),
            justify="left",
            wraplength=800,
            text_color=("gray30", "gray75"),
        ).grid(row=0, column=0, padx=14, pady=12, sticky="w")

    @staticmethod
    def _section(parent: ctk.CTkBaseClass, row: int, text: str) -> None:
        ctk.CTkLabel(
            parent, text=text, font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=row, column=0, sticky="w", pady=(4, 8))

    def _choose_source(self) -> None:
        selected = filedialog.askdirectory(
            title="Choose a folder containing source video clips"
        )
        if selected:
            self.source_var.set(selected)
            self._save_settings()

    def _save_settings(self) -> None:
        self.settings["source_folder"] = self.source_var.get().strip()
        self.settings["target_seconds"] = int(self.length_var.get())
        save_settings(self.settings)

    def _refresh_engine_status(self) -> None:
        ready = executable_available("ffmpeg") and executable_available("ffprobe")
        self.engine_badge.configure(
            text="VIDEO ENGINE READY" if ready else "FFMPEG NEEDED"
        )

    def _start_build(self) -> None:
        if not executable_available("ffmpeg") or not executable_available("ffprobe"):
            messagebox.showerror(
                "FFmpeg required",
                "FFmpeg and ffprobe were not found on PATH. Install FFmpeg, then reopen the app.",
            )
            return

        hook = self.hook_entry.get().strip()
        if not hook:
            messagebox.showwarning("Hook needed", "Enter a hook/title first.")
            return

        source = Path(self.source_var.get().strip())
        if not source.exists():
            messagebox.showwarning("Source folder", "Choose a valid source folder.")
            return

        script = self.script_box.get("1.0", "end").strip()
        self._save_settings()

        request = BuildRequest(
            source_folder=source,
            hook=hook,
            script=script,
            voice=self.settings["voice"],
            target_seconds=int(self.length_var.get()),
            use_voice=self.voice_enabled.get(),
        )

        self.create_button.configure(state="disabled", text="BUILDING...")
        self.open_output_button.configure(state="disabled")
        self.result_label.configure(text="Rendering your Short...")
        self.progress.start()

        threading.Thread(
            target=self._build_worker, args=(request,), daemon=True
        ).start()

    def _build_worker(self, request: BuildRequest) -> None:
        try:
            result = create_short(request)
        except Exception as exc:
            self.after(0, self._build_failed, str(exc))
            return
        self.after(0, self._build_finished, result.output_path, result.clip_count)

    def _build_finished(self, output_path: Path, clip_count: int) -> None:
        self.progress.stop()
        self.progress.set(1)
        self.create_button.configure(state="normal", text="CREATE ANOTHER SHORT")
        self.last_output = output_path
        self.result_label.configure(
            text=f"Done — {clip_count} source clip(s) available.\n{output_path}"
        )
        self.open_output_button.configure(state="normal")

    def _build_failed(self, error: str) -> None:
        self.progress.stop()
        self.progress.set(0)
        self.create_button.configure(state="normal", text="CREATE SHORT")
        self.result_label.configure(text=f"Build failed: {error}")
        messagebox.showerror("Build failed", error)

    def _open_output(self) -> None:
        folder = (
            self.last_output.parent
            if self.last_output is not None
            else Path("output").resolve()
        )
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(folder)


if __name__ == "__main__":
    ShortsFactoryApp().mainloop()
