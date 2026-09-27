from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ManifestAuditResult(BaseModel):
    playlist_type: str  # 'Master' or 'Media'
    target_duration: Optional[float] = None
    total_segments: int
    bitrate_ladder: List[Dict[str, Any]] = []
    discontinuity_count: int
    compliance_passed: bool
    issues_detected: List[str] = []

class AdMarkerAuditResult(BaseModel):
    total_ad_breaks: int
    cue_out_count: int
    cue_in_count: int
    ad_markers_valid: bool
    detected_splices: List[Dict[str, Any]] = []
    ad_insertion_issues: List[str] = []

class QoETriageResult(BaseModel):
    session_id: str
    qoe_health_status: str  # 'HEALTHY', 'DEGRADED', 'CRITICAL_OUTAGE'
    time_to_first_frame_ms: int
    rebuffering_ratio_pct: float
    root_cause_analysis: str
    recommended_mitigation: str
