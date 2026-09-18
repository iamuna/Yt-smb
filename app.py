from __future__ import annotations

import os
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from shorts_factory.ai import ShortPlan, generate_short_plan, ollama_ready
from shorts_factory.automation import AutoRequest, AutoResult, run_auto_short
from shorts_factory.config import ensure_directories, load_settings, save_settings
from shorts_factory.pipeline import BuildRequest, create_short
from shorts_factory.providers import available_source_providers
from shorts_factory.queue import enqueue, list_recent, mark_failed, mark_uploaded, next_pending
from shorts_factory.secrets import (
    get_source_api_key,
    load_secrets,
    save_secrets,
    set_source_api_key,
)
from shorts_factory.utils import executable_available
from shorts_factory.youtube import upload_video

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master: "ShortsFactoryApp") -> None:
        super().__init__(master)
        self.master_app = master
        self.title("YT SMB Settings")
        self.geometry("760x650")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.settings = master.settings.copy()
        self.secrets = load_secrets()
        self.providers = available_source_providers()
        self.provider_names_to_ids = {
            name: provider_id for provider_id, name in self.providers.items()
        }

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="SETTINGS",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(22, 6))

        ctk.CTkLabel(
            self,
            text="Default mode is local/free. Paid-service providers are blocked.",
            text_color=("gray35", "gray70"),
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 14))

        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 18))
        frame.grid_columnconfigure(1, weight=1)

        self.model_var = ctk.StringVar(
            value=str(self.settings.get("ai_model", "qwen2.5:3b"))
        )
        self.ollama_url_var = ctk.StringVar(
            value=str(
                self.settings.get(
                    "ollama_base_url",
                    "http://127.0.0.1:11434",
                )
            )
        )

        provider_id = str(self.settings.get("source_provider", "pexels"))
        provider_display = self.providers.get(provider_id, provider_id)
        self.provider_var = ctk.StringVar(value=provider_display)
        self.active_provider_id = provider_id
        self.provider_key_var = ctk.StringVar(
            value=get_source_api_key(self.secrets, provider_id)
        )

        self.youtube_var = ctk.StringVar(
            value=str(self.secrets.get("youtube_client_secrets", ""))
        )
        self.publish_var = ctk.BooleanVar(
            value=bool(self.settings.get("publish_enabled", False))
        )
        self.privacy_var = ctk.StringVar(
            value=str(self.settings.get("privacy_status", "private"))
        )

        row = 0
        ctk.CTkLabel(frame, text="Local AI model").grid(
            row=row, column=0, sticky="w", padx=14, pady=10
        )
        ctk.CTkEntry(frame, textvariable=self.model_var).grid(
            row=row, column=1, sticky="ew", padx=14, pady=10
        )
        row += 1

        ctk.CTkLabel(frame, text="Ollama URL").grid(
            row=row, column=0, sticky="w", padx=14, pady=10
        )
        ctk.CTkEntry(frame, textvariable=self.ollama_url_var).grid(
            row=row, column=1, sticky="ew", padx=14, pady=10
        )
        row += 1

        ctk.CTkLabel(frame, text="B-roll provider").grid(
            row=row, column=0, sticky="w", padx=14, pady=10
        )
        self.provider_menu = ctk.CTkOptionMenu(
            frame,
            variable=self.provider_var,
            values=list(self.provider_names_to_ids) or ["Pexels"],
            command=self._provider_changed,
            width=180,
        )
        self.provider_menu.grid(
            row=row, column=1, sticky="w", padx=14, pady=10
        )
        row += 1

        ctk.CTkLabel(frame, text="Provider API key").grid(
            row=row, column=0, sticky="w", padx=14, pady=10
        )
        ctk.CTkEntry(
            frame,
            textvariable=self.provider_key_var,
            show="*",
        ).grid(row=row, column=1, sticky="ew", padx=14, pady=10)
        row += 1

        ctk.CTkLabel(
            frame,
            text=(
                "The B-roll provider is replaceable. New services plug into "
                "shorts_factory/providers/ without changing the editor."
            ),
            justify="left",
            wraplength=560,
            text_color=("gray30", "gray75"),
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            padx=14,
            pady=(0, 10),
        )
        row += 1

        ctk.CTkLabel(frame, text="YouTube OAuth JSON").grid(
            row=row, column=0, sticky="w", padx=14, pady=10
        )
        yt_row = ctk.CTkFrame(frame, fg_color="transparent")
        yt_row.grid(row=row, column=1, sticky="ew", padx=14, pady=10)
        yt_row.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(yt_row, textvariable=self.youtube_var).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ctk.CTkButton(
            yt_row,
            text="Browse",
            width=90,
            command=self._choose_youtube_json,
        ).grid(row=0, column=1)
        row += 1

        ctk.CTkLabel(frame, text="Upload privacy").grid(
            row=row, column=0, sticky="w", padx=14, pady=10
        )
        ctk.CTkOptionMenu(
            frame,
            variable=self.privacy_var,
            values=["private", "unlisted", "public"],
            width=150,
        ).grid(row=row, column=1, sticky="w", padx=14, pady=10)
        row += 1

        ctk.CTkCheckBox(
            frame,
            text="Automatically upload after AUTO MAKE SHORT",
            variable=self.publish_var,
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            padx=14,
            pady=(14, 6),
        )
        row += 1

        ctk.CTkLabel(
            frame,
            text=(
                "Auto-upload is OFF by default. Local AI and local narration do "
                "not use metered cloud APIs. External providers never fall back "
                "to a paid service automatically."
            ),
            justify="left",
            wraplength=620,
            text_color=("gray30", "gray75"),
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            padx=14,
            pady=(2, 14),
        )

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 22))
        buttons.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            buttons,
            text="SAVE",
            height=44,
            command=self._save,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(
            buttons,
            text="Cancel",
            width=120,
            command=self.destroy,
        ).grid(row=0, column=1)

    def _current_provider_id(self) -> str:
        display = self.provider_var.get()
        return self.provider_names_to_ids.get(display, display.lower())

    def _provider_changed(self, _display_name: str) -> None:
        self.secrets = set_source_api_key(
            self.secrets,
            self.active_provider_id,
            self.provider_key_var.get(),
        )
        provider_id = self._current_provider_id()
        self.active_provider_id = provider_id
        self.provider_key_var.set(
            get_source_api_key(self.secrets, provider_id)
        )

    def _choose_youtube_json(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose Google OAuth client secrets JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            self.youtube_var.set(path)

    def _save(self) -> None:
        provider_id = self._current_provider_id()
        self.active_provider_id = provider_id
        updated_secrets = set_source_api_key(
            self.secrets,
            provider_id,
            self.provider_key_var.get(),
        )
        updated_secrets["youtube_client_secrets"] = self.youtube_var.get().strip()
        save_secrets(updated_secrets)

        self.master_app.settings["ai_provider"] = "ollama"
        self.master_app.settings["ai_model"] = (
            self.model_var.get().strip() or "qwen2.5:3b"
        )
        self.master_app.settings["ollama_base_url"] = (
            self.ollama_url_var.get().strip()
            or "http://127.0.0.1:11434"
        )
        self.master_app.settings["source_provider"] = provider_id
        self.master_app.settings["publish_enabled"] = self.publish_var.get()
        self.master_app.settings["privacy_status"] = self.privacy_var.get()
        self.master_app.settings["allow_paid_services"] = False
        save_settings(self.master_app.settings)
        self.master_app.settings = load_settings()
        self.master_app._refresh_status()
        self.master_app._refresh_queue_status()
        self.destroy()


class ShortsFactoryApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ensure_directories()
        self.settings = load_settings()
        self.last_output: Path | None = None
        self.current_plan: ShortPlan | None = None

        self.title("YT SMB — Shorts Factory")
        self.geometry("1050x850")
        self.minsize(900, 700)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._refresh_status()
        self._refresh_queue_status()

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
            text=(
                "FREE LOCAL MODE • topic → local AI → B-roll → local voice → "
                "captions → queue → YouTube"
            ),
            text_color=("gray35", "gray70"),
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        self.engine_badge = ctk.CTkLabel(
            header,
            text="CHECKING...",
            corner_radius=12,
            padx=12,
            pady=6,
        )
        self.engine_badge.grid(row=0, column=1, rowspan=2, padx=(10, 8))

        ctk.CTkButton(
            header,
            text="Settings",
            width=100,
            command=lambda: SettingsDialog(self),
        ).grid(row=0, column=2, rowspan=2, padx=(0, 24))

    def _build_body(self) -> None:
        main = ctk.CTkScrollableFrame(self)
        main.grid(row=1, column=0, sticky="nsew", padx=18, pady=18)
        main.grid_columnconfigure(0, weight=1)

        self._section(main, 0, "1  What should the Short be about?")
        topic_row = ctk.CTkFrame(main)
        topic_row.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        topic_row.grid_columnconfigure(0, weight=1)

        self.topic_entry = ctk.CTkEntry(
            topic_row,
            height=44,
            placeholder_text=(
                "Example: weird space facts, Roman engineering, gaming history..."
            ),
        )
        self.topic_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(12, 8),
            pady=12,
        )
        self.plan_button = ctk.CTkButton(
            topic_row,
            text="LOCAL AI PLAN",
            width=140,
            command=self._start_plan,
        )
        self.plan_button.grid(row=0, column=1, padx=(0, 12), pady=12)

        self._section(main, 2, "2  Local source clips (optional)")
        source_row = ctk.CTkFrame(main)
        source_row.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        source_row.grid_columnconfigure(0, weight=1)

        self.source_var = ctk.StringVar(value=self.settings["source_folder"])
        ctk.CTkEntry(
            source_row,
            textvariable=self.source_var,
            height=42,
        ).grid(row=0, column=0, sticky="ew", padx=(12, 8), pady=12)
        ctk.CTkButton(
            source_row,
            text="Choose folder",
            width=135,
            command=self._choose_source,
        ).grid(row=0, column=1, padx=(0, 12), pady=12)

        self._section(main, 4, "3  Hook")
        self.hook_entry = ctk.CTkEntry(
            main,
            height=44,
            placeholder_text="Local AI will fill this, or type your own.",
        )
        self.hook_entry.grid(row=5, column=0, sticky="ew", pady=(0, 14))

        self._section(main, 6, "4  Narration")
        self.script_box = ctk.CTkTextbox(main, height=165)
        self.script_box.grid(row=7, column=0, sticky="ew", pady=(0, 14))

        options = ctk.CTkFrame(main)
        options.grid(row=8, column=0, sticky="ew", pady=(0, 14))
        options.grid_columnconfigure(0, weight=1)

        self.voice_enabled = ctk.BooleanVar(value=True)
        self.online_sources_enabled = ctk.BooleanVar(
            value=bool(self.settings.get("use_online_sources", True))
        )
        self.queue_enabled = ctk.BooleanVar(
            value=bool(self.settings.get("auto_queue", True))
        )

        ctk.CTkCheckBox(
            options,
            text="Local voice-over",
            variable=self.voice_enabled,
        ).grid(row=0, column=0, padx=14, pady=12, sticky="w")

        self.online_source_checkbox = ctk.CTkCheckBox(
            options,
            text="Online B-roll",
            variable=self.online_sources_enabled,
        )
        self.online_source_checkbox.grid(
            row=0, column=1, padx=14, pady=12, sticky="w"
        )

        ctk.CTkCheckBox(
            options,
            text="Add to upload queue",
            variable=self.queue_enabled,
        ).grid(row=0, column=2, padx=14, pady=12, sticky="w")

        ctk.CTkLabel(options, text="Length").grid(
            row=0, column=3, padx=(14, 4), pady=12
        )
        self.length_var = ctk.StringVar(
            value=str(self.settings["target_seconds"])
        )
        ctk.CTkOptionMenu(
            options,
            variable=self.length_var,
            values=["15", "25", "35", "45", "60"],
            width=90,
        ).grid(row=0, column=4, padx=(4, 14), pady=12)

        actions = ctk.CTkFrame(main, fg_color="transparent")
        actions.grid(row=9, column=0, sticky="ew", pady=(0, 12))
        actions.grid_columnconfigure((0, 1), weight=1)

        self.auto_button = ctk.CTkButton(
            actions,
            text="AUTO MAKE SHORT",
            height=60,
            font=ctk.CTkFont(size=20, weight="bold"),
            command=self._start_auto,
        )
        self.auto_button.grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )

        self.create_button = ctk.CTkButton(
            actions,
            text="CREATE FROM CURRENT",
            height=60,
            command=self._start_manual_build,
        )
        self.create_button.grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        self.progress = ctk.CTkProgressBar(main, mode="indeterminate")
        self.progress.grid(row=10, column=0, sticky="ew", pady=(0, 10))
        self.progress.stop()
        self.progress.set(0)

        self.result_label = ctk.CTkLabel(
            main,
            text="Ready.",
            anchor="w",
            justify="left",
            wraplength=900,
        )
        self.result_label.grid(row=11, column=0, sticky="ew", pady=(0, 10))

        bottom = ctk.CTkFrame(main)
        bottom.grid(row=12, column=0, sticky="ew", pady=(0, 12))
        bottom.grid_columnconfigure(2, weight=1)

        self.open_output_button = ctk.CTkButton(
            bottom,
            text="Open output",
            command=self._open_output,
            state="disabled",
        )
        self.open_output_button.grid(row=0, column=0, padx=12, pady=12)

        self.upload_button = ctk.CTkButton(
            bottom,
            text="UPLOAD NEXT",
            command=self._start_upload_next,
        )
        self.upload_button.grid(
            row=0, column=1, padx=(0, 12), pady=12
        )

        self.queue_label = ctk.CTkLabel(
            bottom,
            text="Queue: checking...",
            anchor="e",
        )
        self.queue_label.grid(
            row=0, column=2, sticky="e", padx=12, pady=12
        )

        self.cost_label = ctk.CTkLabel(
            main,
            text=(
                "Cost guard: PAID SERVICES BLOCKED. Local AI and local speech "
                "are the default. Online source failures stop instead of "
                "switching to a paid provider."
            ),
            justify="left",
            text_color=("gray30", "gray75"),
            wraplength=900,
        )
        self.cost_label.grid(
            row=13, column=0, sticky="w", pady=(0, 12)
        )

    @staticmethod
    def _section(parent: ctk.CTkBaseClass, row: int, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=18, weight="bold"),
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
        self.settings["use_online_sources"] = self.online_sources_enabled.get()
        self.settings["auto_queue"] = self.queue_enabled.get()
        self.settings["allow_paid_services"] = False
        save_settings(self.settings)

    def _refresh_status(self) -> None:
        video_ready = (
            executable_available("ffmpeg")
            and executable_available("ffprobe")
        )
        ai_ready = ollama_ready(
            str(
                self.settings.get(
                    "ollama_base_url",
                    "http://127.0.0.1:11434",
                )
            )
        )

        if video_ready and ai_ready:
            text = "LOCAL STACK READY"
        elif not video_ready and not ai_ready:
            text = "FFMPEG + OLLAMA NEEDED"
        elif not video_ready:
            text = "FFMPEG NEEDED"
        else:
            text = "OLLAMA NEEDED"
        self.engine_badge.configure(text=text)

        provider_id = str(
            self.settings.get("source_provider", "pexels")
        )
        provider_name = available_source_providers().get(
            provider_id,
            provider_id,
        )
        self.online_source_checkbox.configure(
            text=f"Online B-roll ({provider_name})"
        )

    def _refresh_queue_status(self) -> None:
        items = list_recent(100)
        pending = sum(1 for item in items if item.status == "pending")
        uploaded = sum(1 for item in items if item.status == "uploaded")
        auto = (
            "ON"
            if self.settings.get("publish_enabled", False)
            else "OFF"
        )
        self.queue_label.configure(
            text=(
                f"Queue: {pending} pending • {uploaded} uploaded • "
                f"Auto-upload: {auto}"
            )
        )

    def _set_busy(self, message: str) -> None:
        self.auto_button.configure(state="disabled")
        self.create_button.configure(state="disabled")
        self.plan_button.configure(state="disabled")
        self.upload_button.configure(state="disabled")
        self.result_label.configure(text=message)
        self.progress.start()

    def _clear_busy(self) -> None:
        self.progress.stop()
        self.progress.set(0)
        self.auto_button.configure(state="normal")
        self.create_button.configure(state="normal")
        self.plan_button.configure(state="normal")
        self.upload_button.configure(state="normal")

    def _require_video_engine(self) -> bool:
        if (
            executable_available("ffmpeg")
            and executable_available("ffprobe")
        ):
            return True
        messagebox.showerror(
            "FFmpeg required",
            "FFmpeg and ffprobe were not found on PATH. Run setup.bat again.",
        )
        return False

    def _require_local_ai(self) -> bool:
        base_url = str(
            self.settings.get(
                "ollama_base_url",
                "http://127.0.0.1:11434",
            )
        )
        if ollama_ready(base_url):
            return True
        messagebox.showerror(
            "Local AI required",
            (
                "Ollama is not running. Run setup.bat, or install/start "
                "Ollama and pull the configured model. No paid API key is needed."
            ),
        )
        return False

    def _start_plan(self) -> None:
        topic = self.topic_entry.get().strip()
        if not topic:
            messagebox.showwarning(
                "Topic needed",
                "Type a topic or niche first.",
            )
            return
        if not self._require_local_ai():
            return

        self._save_settings()
        self._set_busy(
            "Local AI is creating the idea, script, metadata, and B-roll terms..."
        )
        threading.Thread(
            target=self._plan_worker,
            args=(topic,),
            daemon=True,
        ).start()

    def _plan_worker(self, topic: str) -> None:
        try:
            plan = generate_short_plan(
                topic=topic,
                target_seconds=int(self.length_var.get()),
                model=str(
                    self.settings.get("ai_model", "qwen2.5:3b")
                ),
                base_url=str(
                    self.settings.get(
                        "ollama_base_url",
                        "http://127.0.0.1:11434",
                    )
                ),
                allow_paid_services=False,
            )
        except Exception as exc:
            self.after(0, self._failed, str(exc))
            return
        self.after(0, self._plan_finished, plan)

    def _plan_finished(self, plan: ShortPlan) -> None:
        self._clear_busy()
        self.current_plan = plan
        self.hook_entry.delete(0, "end")
        self.hook_entry.insert(0, plan.hook)
        self.script_box.delete("1.0", "end")
        self.script_box.insert("1.0", plan.script)
        self.result_label.configure(
            text=(
                f"Local AI plan ready.\nTitle: {plan.title}\n"
                f"B-roll searches: {', '.join(plan.search_terms)}"
            )
        )

    def _start_auto(self) -> None:
        if not self._require_video_engine():
            return
        if not self._require_local_ai():
            return

        topic = self.topic_entry.get().strip()
        if not topic:
            messagebox.showwarning(
                "Topic needed",
                "Type a topic or niche first.",
            )
            return

        self._save_settings()
        request = AutoRequest(
            topic=topic,
            source_folder=Path(self.source_var.get().strip()),
            target_seconds=int(self.length_var.get()),
            voice=str(self.settings.get("voice", "default")),
            use_voice=self.voice_enabled.get(),
            use_online_sources=self.online_sources_enabled.get(),
            source_provider=str(
                self.settings.get("source_provider", "pexels")
            ),
            auto_queue=self.queue_enabled.get(),
            privacy_status=str(
                self.settings.get("privacy_status", "private")
            ),
            ai_model=str(
                self.settings.get("ai_model", "qwen2.5:3b")
            ),
            ollama_base_url=str(
                self.settings.get(
                    "ollama_base_url",
                    "http://127.0.0.1:11434",
                )
            ),
            allow_paid_services=False,
        )
        self._set_busy(
            "AUTO: local AI → permitted B-roll → local voice → captions → render..."
        )
        threading.Thread(
            target=self._auto_worker,
            args=(request,),
            daemon=True,
        ).start()

    def _auto_worker(self, request: AutoRequest) -> None:
        try:
            result = run_auto_short(request)
            uploaded_id = None

            if self.settings.get("publish_enabled", False):
                secrets = load_secrets()
                client_value = str(
                    secrets.get("youtube_client_secrets", "")
                ).strip()
                client_file = (
                    Path(client_value) if client_value else None
                )
                if client_file is None or not client_file.is_file():
                    raise RuntimeError(
                        "Auto-upload is enabled, but the YouTube OAuth "
                        "JSON file is missing."
                    )

                uploaded_id = upload_video(
                    video_path=result.build.output_path,
                    title=result.plan.title or result.plan.hook,
                    description=result.plan.description,
                    tags=result.plan.tags,
                    privacy_status=str(
                        self.settings.get(
                            "privacy_status",
                            "private",
                        )
                    ),
                    client_secrets_file=client_file,
                )
                if result.queue_id is not None:
                    mark_uploaded(
                        result.queue_id,
                        uploaded_id,
                    )

        except Exception as exc:
            self.after(0, self._failed, str(exc))
            return

        self.after(
            0,
            self._auto_finished,
            result,
            uploaded_id,
        )

    def _auto_finished(
        self,
        result: AutoResult,
        uploaded_id: str | None,
    ) -> None:
        self._clear_busy()
        self.current_plan = result.plan
        self.last_output = result.build.output_path

        self.hook_entry.delete(0, "end")
        self.hook_entry.insert(0, result.plan.hook)
        self.script_box.delete("1.0", "end")
        self.script_box.insert("1.0", result.plan.script)

        providers = sorted({asset.provider for asset in result.sources})
        source_note = (
            f"{len(result.sources)} online clip(s) from "
            f"{', '.join(providers)} + local clips"
            if result.sources
            else "local clips only"
        )
        queue_note = (
            f"Queue #{result.queue_id}"
            if result.queue_id is not None
            else "not queued"
        )
        upload_note = (
            f"Uploaded: https://youtu.be/{uploaded_id}"
            if uploaded_id
            else "not auto-uploaded"
        )

        self.result_label.configure(
            text=(
                f"DONE — {result.plan.title}\n"
                f"Sources: {source_note} • {queue_note}\n"
                f"{upload_note}\n"
                f"{result.build.output_path}"
            )
        )
        self.open_output_button.configure(state="normal")
        self._refresh_queue_status()

    def _start_manual_build(self) -> None:
        if not self._require_video_engine():
            return

        hook = self.hook_entry.get().strip()
        if not hook:
            messagebox.showwarning(
                "Hook needed",
                "Enter a hook or use LOCAL AI PLAN.",
            )
            return

        source = Path(self.source_var.get().strip())
        if not source.exists():
            messagebox.showwarning(
                "Source folder",
                "Choose a valid local source folder.",
            )
            return

        script = self.script_box.get("1.0", "end").strip()
        self._save_settings()

        request = BuildRequest(
            source_folder=source,
            hook=hook,
            script=script,
            voice=str(self.settings.get("voice", "default")),
            target_seconds=int(self.length_var.get()),
            use_voice=self.voice_enabled.get(),
            captions=True,
            allow_paid_services=False,
        )

        self._set_busy(
            "Rendering your Short with local voice and captions..."
        )
        threading.Thread(
            target=self._manual_worker,
            args=(request,),
            daemon=True,
        ).start()

    def _manual_worker(self, request: BuildRequest) -> None:
        try:
            result = create_short(request)
            queue_id = None
            if self.queue_enabled.get():
                if self.current_plan:
                    title = self.current_plan.title or request.hook
                    description = self.current_plan.description
                    tags = self.current_plan.tags
                else:
                    title = request.hook
                    description = "#Shorts"
                    tags = ["Shorts"]

                queue_id = enqueue(
                    result.output_path,
                    title,
                    description,
                    tags,
                    str(
                        self.settings.get(
                            "privacy_status",
                            "private",
                        )
                    ),
                )
        except Exception as exc:
            self.after(0, self._failed, str(exc))
            return

        self.after(
            0,
            self._manual_finished,
            result.output_path,
            queue_id,
        )

    def _manual_finished(
        self,
        output_path: Path,
        queue_id: int | None,
    ) -> None:
        self._clear_busy()
        self.last_output = output_path
        queue_text = (
            f" • Queue #{queue_id}"
            if queue_id is not None
            else ""
        )
        self.result_label.configure(
            text=f"Done{queue_text}\n{output_path}"
        )
        self.open_output_button.configure(state="normal")
        self._refresh_queue_status()

    def _start_upload_next(self) -> None:
        item = next_pending()
        if item is None:
            messagebox.showinfo(
                "Upload queue",
                "There are no pending videos.",
            )
            return

        secrets = load_secrets()
        client_value = str(
            secrets.get("youtube_client_secrets", "")
        ).strip()
        client_file = Path(client_value) if client_value else None
        if client_file is None or not client_file.is_file():
            messagebox.showwarning(
                "YouTube not connected",
                (
                    "Open Settings and choose your Google OAuth client "
                    "secrets JSON first."
                ),
            )
            return

        if not messagebox.askyesno(
            "Upload to YouTube",
            (
                f"Upload queue #{item.id} as "
                f"{item.privacy_status}?\n\n{item.title}"
            ),
        ):
            return

        self._set_busy(
            f"Uploading queue #{item.id} to YouTube..."
        )
        threading.Thread(
            target=self._upload_worker,
            args=(
                item.id,
                item.video_path,
                item.title,
                item.description,
                item.tags,
                item.privacy_status,
                client_file,
            ),
            daemon=True,
        ).start()

    def _upload_worker(
        self,
        item_id: int,
        video_path: str,
        title: str,
        description: str,
        tags: list[str],
        privacy_status: str,
        client_file: Path,
    ) -> None:
        try:
            video_id = upload_video(
                video_path=Path(video_path),
                title=title,
                description=description,
                tags=tags,
                privacy_status=privacy_status,
                client_secrets_file=client_file,
            )
            mark_uploaded(item_id, video_id)
        except Exception as exc:
            mark_failed(item_id)
            self.after(0, self._failed, str(exc))
            return

        self.after(
            0,
            self._upload_finished,
            item_id,
            video_id,
        )

    def _upload_finished(
        self,
        item_id: int,
        video_id: str,
    ) -> None:
        self._clear_busy()
        self.result_label.configure(
            text=(
                f"Queue #{item_id} uploaded successfully.\n"
                f"https://youtu.be/{video_id}"
            )
        )
        self._refresh_queue_status()

    def _failed(self, error: str) -> None:
        self._clear_busy()
        self.result_label.configure(text=f"Error: {error}")
        messagebox.showerror("YT SMB", error)
        self._refresh_queue_status()

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
