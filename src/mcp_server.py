import json
import re
from typing import Dict, Any, List, Optional
from src.models import ManifestAuditResult, AdMarkerAuditResult, QoETriageResult

class StreamingTelemetryMCPServer:
    """A Model Context Protocol (MCP) Server providing AI agents with
    video streaming diagnostic and telemetry tools.
    """
    SERVER_NAME = "StreamingTelemetryMCP"
    PROTOCOL_VERSION = "2024-11-05"

    def list_tools(self) -> List[Dict[str, Any]]:
        """MCP standard: Returns available tools and their JSON schemas."""
        return [
            {
                "name": "inspect_hls_manifest",
                "description": "Parses HLS m3u8 playlists, audits bitrate ladders, target durations, and flags discontinuities.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "manifest_content": {"type": "string", "description": "Raw m3u8 manifest text"}
                    },
                    "required": ["manifest_content"]
                }
            },
            {
                "name": "validate_ad_markers",
                "description": "Audits SCTE-35, EXT-X-DATERANGE, and CUE tags for SSAI ad insertion alignment.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "manifest_content": {"type": "string", "description": "Raw m3u8 manifest containing ad tags"}
                    },
                    "required": ["manifest_content"]
                }
            },
            {
                "name": "query_stream_qoe",
                "description": "Evaluates playback session telemetry (TTFF, rebuffering, error codes) and outputs Root Cause Analysis.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "startup_time_ms": {"type": "integer"},
                        "rebuffering_ratio_pct": {"type": "number"},
                        "cdn_edge_pop": {"type": "string"},
                        "error_code": {"type": "string"}
                    },
                    "required": ["session_id", "startup_time_ms", "rebuffering_ratio_pct"]
                }
            }
        ]

    # --- Tool 1: Inspect HLS Manifest ---
    def inspect_hls_manifest(self, manifest_content: str) -> ManifestAuditResult:
        lines = [line.strip() for line in manifest_content.strip().split("\n") if line.strip()]
        is_master = any("#EXT-X-STREAM-INF" in line for line in lines)
        
        bitrate_ladder = []
        issues = []
        target_duration = None
        discontinuities = 0
        segments = 0

        if is_master:
            for line in lines:
                if line.startswith("#EXT-X-STREAM-INF"):
                    bw_match = re.search(r'BANDWIDTH=(\d+)', line)
                    res_match = re.search(r'RESOLUTION=(\d+x\d+)', line)
                    bw = int(bw_match.group(1)) if bw_match else 0
                    res = res_match.group(1) if res_match else "Unknown"
                    bitrate_ladder.append({"bandwidth_bps": bw, "resolution": res})
            
            sorted_ladder = sorted(bitrate_ladder, key=lambda x: x["bandwidth_bps"])
            for idx in range(len(sorted_ladder) - 1):
                ratio = sorted_ladder[idx+1]["bandwidth_bps"] / max(sorted_ladder[idx]["bandwidth_bps"], 1)
                if ratio > 2.5:
                    issues.append(f"Aggressive bitrate step ({ratio:.1f}x) between {sorted_ladder[idx]['resolution']} and {sorted_ladder[idx+1]['resolution']} risk causing player stalls.")

            return ManifestAuditResult(
                playlist_type="Master",
                total_segments=0,
                bitrate_ladder=sorted_ladder,
                discontinuity_count=0,
                compliance_passed=len(issues) == 0,
                issues_detected=issues
            )
        else:
            for line in lines:
                if line.startswith("#EXT-X-TARGETDURATION:"):
                    target_duration = float(line.split(":"))
                elif line.startswith("#EXT-X-DISCONTINUITY"):
                    discontinuities += 1
                elif line.startswith("#EXTINF:"):
                    segments += 1
                    dur = float(line.split(":").split(",")[0])
                    if target_duration and dur > (target_duration + 0.5):
                        issues.append(f"Segment duration ({dur}s) exceeds #EXT-X-TARGETDURATION ({target_duration}s).")

            return ManifestAuditResult(
                playlist_type="Media",
                target_duration=target_duration,
                total_segments=segments,
                bitrate_ladder=[],
                discontinuity_count=discontinuities,
                compliance_passed=len(issues) == 0,
                issues_detected=issues
            )

    # --- Tool 2: Validate Ad Markers ---
    def validate_ad_markers(self, manifest_content: str) -> AdMarkerAuditResult:
        lines = [line.strip() for line in manifest_content.strip().split("\n") if line.strip()]
        cue_outs = sum(1 for line in lines if "CUE-OUT" in line)
        cue_ins = sum(1 for line in lines if "CUE-IN" in line)
        dateranges = [line for line in lines if line.startswith("#EXT-X-DATERANGE")]
        
        issues = []
        if cue_outs != cue_ins:
            issues.append(f"Mismatched Ad Cues: Found {cue_outs} CUE-OUT tags but {cue_ins} CUE-IN tags (potential unclosed ad splice).")
        
        splices = []
        for dr in dateranges:
            id_match = re.search(r'ID="([^"]+)"', dr)
            dur_match = re.search(r'PLANNED-DURATION=([\d\.]+)', dr)
            splices.append({
                "splice_id": id_match.group(1) if id_match else "UNKNOWN",
                "planned_duration_sec": float(dur_match.group(1)) if dur_match else 0.0
            })

        return AdMarkerAuditResult(
            total_ad_breaks=max(cue_outs, len(dateranges)),
            cue_out_count=cue_outs,
            cue_in_count=cue_ins,
            ad_markers_valid=len(issues) == 0,
            detected_splices=splices,
            ad_insertion_issues=issues
        )

    # --- Tool 3: Query Stream QoE ---
    def query_stream_qoe(self, session_id: str, startup_time_ms: int, rebuffering_ratio_pct: float, cdn_edge_pop: str = "EWR-01", error_code: Optional[str] = None) -> QoETriageResult:
        if error_code in ["CDN_504", "HTTP_503"]:
            return QoETriageResult(
                session_id=session_id,
                qoe_health_status="CRITICAL_OUTAGE",
                time_to_first_frame_ms=startup_time_ms,
                rebuffering_ratio_pct=rebuffering_ratio_pct,
                root_cause_analysis=f"Critical playback failure triggered by {error_code} gateway timeout at CDN Edge POP '{cdn_edge_pop}'.",
                recommended_mitigation="Trigger automated multi-CDN failover traffic steering to secondary CDN provider."
            )
        elif rebuffering_ratio_pct > 1.0 or startup_time_ms > 4000:
            return QoETriageResult(
                session_id=session_id,
                qoe_health_status="DEGRADED",
                time_to_first_frame_ms=startup_time_ms,
                rebuffering_ratio_pct=rebuffering_ratio_pct,
                root_cause_analysis=f"Elevated rebuffering ({rebuffering_ratio_pct}%) and startup delay ({startup_time_ms}ms) detected on POP '{cdn_edge_pop}'. Likely edge cache miss or bandwidth ladder mismatch.",
                recommended_mitigation="Instruct player ABR algorithms to start on lower initial bitrate rendition (e.g. 720p)."
            )
        else:
            return QoETriageResult(
                session_id=session_id,
                qoe_health_status="HEALTHY",
                time_to_first_frame_ms=startup_time_ms,
                rebuffering_ratio_pct=rebuffering_ratio_pct,
                root_cause_analysis="Session metrics meet all streaming broadcast SLAs. No incident detected.",
                recommended_mitigation="No mitigation required."
            )
