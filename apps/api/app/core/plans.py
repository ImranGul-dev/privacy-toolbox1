from __future__ import annotations

from dataclasses import dataclass, asdict, replace
from pathlib import Path
from typing import Literal

PlanName = Literal['free', 'pro', 'team', 'business']
FileFamily = Literal['image', 'pdf', 'office', 'zip', 'audio', 'video', 'other']

@dataclass(frozen=True)
class PlanLimits:
    name: PlanName
    label: str
    daily_scans: int
    daily_cleans: int
    monthly_files: int
    batch_files: int
    priority: int
    history_days: int
    audit_reports: bool
    advanced_pdf: bool
    api_access: bool
    file_mb: dict[str, int]

PLANS: dict[PlanName, PlanLimits] = {
    'free': PlanLimits(
        name='free', label='Free', daily_scans=5, daily_cleans=3, monthly_files=60,
        batch_files=1, priority=0, history_days=0, audit_reports=False, advanced_pdf=False, api_access=False,
        file_mb={'image': 25, 'pdf': 50, 'office': 50, 'zip': 50, 'audio': 50, 'video': 100, 'other': 25},
    ),
    'pro': PlanLimits(
        name='pro', label='Pro', daily_scans=100, daily_cleans=100, monthly_files=100,
        batch_files=10, priority=1, history_days=7, audit_reports=True, advanced_pdf=True, api_access=False,
        file_mb={'image': 100, 'pdf': 200, 'office': 200, 'zip': 250, 'audio': 250, 'video': 512, 'other': 100},
    ),
    'team': PlanLimits(
        name='team', label='Team', daily_scans=500, daily_cleans=500, monthly_files=500,
        batch_files=50, priority=2, history_days=30, audit_reports=True, advanced_pdf=True, api_access=False,
        file_mb={'image': 200, 'pdf': 500, 'office': 500, 'zip': 512, 'audio': 512, 'video': 512, 'other': 200},
    ),
    'business': PlanLimits(
        name='business', label='Business/API', daily_scans=2500, daily_cleans=2500, monthly_files=2000,
        batch_files=100, priority=3, history_days=90, audit_reports=True, advanced_pdf=True, api_access=True,
        file_mb={'image': 300, 'pdf': 512, 'office': 512, 'zip': 512, 'audio': 512, 'video': 512, 'other': 300},
    ),
}

EXTENSION_FAMILIES: dict[str, FileFamily] = {
    '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.webp': 'image', '.tif': 'image', '.tiff': 'image', '.heic': 'image',
    '.pdf': 'pdf',
    '.docx': 'office', '.xlsx': 'office', '.pptx': 'office',
    '.zip': 'zip',
    '.mp3': 'audio', '.m4a': 'audio', '.wav': 'audio', '.flac': 'audio', '.ogg': 'audio',
    '.mp4': 'video', '.mov': 'video', '.m4v': 'video', '.avi': 'video', '.mkv': 'video', '.webm': 'video',
}

ACTION_COST = {'scan': 'scan', 'verify': 'scan', 'clean': 'clean'}


def plan_dict(plan: PlanLimits) -> dict:
    return asdict(plan)


def get_plan(name: str | None) -> PlanLimits:
    key = (name or 'free').lower()
    if key not in PLANS:
        key = 'free'
    base = PLANS[key]  # type: ignore[index]
    try:
        from app.services.admin_config_service import effective_plan
        cfg = effective_plan(key)
        return replace(
            base,
            label=str(cfg.get('label') or base.label),
            daily_scans=int(cfg.get('daily_scans', base.daily_scans)),
            daily_cleans=int(cfg.get('daily_cleans', base.daily_cleans)),
            monthly_files=int(cfg.get('monthly_files', base.monthly_files)),
            batch_files=int(cfg.get('batch_files', base.batch_files)),
            history_days=int(cfg.get('history_days', base.history_days)),
            audit_reports=bool(cfg.get('audit_reports', base.audit_reports)),
            advanced_pdf=bool(cfg.get('advanced_pdf', base.advanced_pdf)),
            api_access=bool(cfg.get('api_access', base.api_access)),
            file_mb={**base.file_mb, **dict(cfg.get('file_mb') or {})},
        )
    except Exception:
        return base


def family_for_path(path: Path) -> FileFamily:
    return EXTENSION_FAMILIES.get(path.suffix.lower(), 'other')


def limit_mb_for(plan_name: str | None, family: str) -> int:
    plan = get_plan(plan_name)
    return plan.file_mb.get(family, plan.file_mb['other'])


def limit_exceeded_message(*, plan_name: str, family: str, size_bytes: int, limit_mb: int) -> str:
    size_mb = size_bytes / (1024 * 1024)
    return (
        f"This {family} file is {size_mb:.1f} MB, which exceeds the {get_plan(plan_name).label} plan limit of {limit_mb} MB. "
        "Upload a smaller file or upgrade your plan for higher file-size limits."
    )
