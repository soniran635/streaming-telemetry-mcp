import os
import sys

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import json
from src.mcp_server import StreamingTelemetryMCPServer

st.set_page_config(page_title="StreamingTelemetry-MCP | Protocol Server", layout="wide", page_icon="📡")

st.title("📡 StreamingTelemetry-MCP: Model Context Protocol Server")
st.markdown("**Anthropic MCP Spec (2024-11-05) | Video Playback Telemetry & HLS Stream Inspection** | *100% Free & Open-Source*")

server = StreamingTelemetryMCPServer()

tab1, tab2, tab3, tab4 = st.tabs([
    "🎬 Tool 1: HLS Manifest Inspector",
    "🎯 Tool 2: SSAI Ad Marker Validator",
    "🚨 Tool 3: Playback QoE Incident Triager",
    "📜 Live MCP JSON-RPC Schemas"
])

# ----------------- TAB 1: HLS MANIFEST INSPECTOR -----------------
with tab1:
    st.subheader("Tool: `inspect_hls_manifest`")
    st.caption("Audits bitrate ladders, segment duration conformance, and discontinuity tags.")

    sample_master = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:6\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,CODECS=\"avc1.4d401f,mp4a.40.2\"\n"
        "360p.m3u8\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=2400000,RESOLUTION=1280x720,CODECS=\"avc1.4d401f,mp4a.40.2\"\n"
        "720p.m3u8\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=7500000,RESOLUTION=1920x1080,CODECS=\"avc1.640028,mp4a.40.2\"\n"
        "1080p.m3u8\n"
    )

    manifest_input = st.text_area("HLS Playlist Content (.m3u8)", sample_master, height=200)
    if st.button("⚡ Execute `inspect_hls_manifest`", type="primary"):
        res = server.inspect_hls_manifest(manifest_input)
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Playlist Type", res.playlist_type)
            st.metric("Compliance Status", "PASSED" if res.compliance_passed else "WARNINGS FLAGGED")
        with c2:
            if res.bitrate_ladder:
                st.markdown("**Bitrate Ladder Steps:**")
                st.dataframe(res.bitrate_ladder, use_container_width=True)

        if res.issues_detected:
            st.warning("**Issues Detected:**")
            for issue in res.issues_detected:
                st.markdown(f"- ⚠️ {issue}")
        else:
            st.success("✅ All bitrate steps and target durations comply with streaming standards.")

# ----------------- TAB 2: AD MARKER VALIDATOR -----------------
with tab2:
    st.subheader("Tool: `validate_ad_markers`")
    st.caption("Audits SCTE-35 and EXT-X-DATERANGE tags for Server-Side Ad Insertion (SSAI).")

    sample_ad_manifest = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:6\n"
        "#EXT-X-TARGETDURATION:6\n"
        "#EXTINF:6.0,\n"
        "segment_01.ts\n"
        "#EXT-X-DATERANGE:ID=\"splice-ad-01\",START-DATE=\"2026-09-27T19:00:00Z\",PLANNED-DURATION=30.0\n"
        "#EXT-X-CUE-OUT:DURATION=30.0\n"
        "#EXTINF:6.0,\n"
        "ad_segment_01.ts\n"
        "#EXTINF:6.0,\n"
        "ad_segment_02.ts\n"
        "#EXT-X-CUE-IN\n"
        "#EXTINF:6.0,\n"
        "segment_02.ts\n"
    )

    ad_input = st.text_area("Manifest with Ad Tags (.m3u8)", sample_ad_manifest, height=200)
    if st.button("⚡ Execute `validate_ad_markers`", type="primary"):
        ad_res = server.validate_ad_markers(ad_input)
        
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Total Ad Breaks", ad_res.total_ad_breaks)
        with k2:
            st.metric("CUE Splice Pairs", f"{ad_res.cue_out_count} OUT / {ad_res.cue_in_count} IN")
        with k3:
            st.metric("Ad Markers Valid", "YES" if ad_res.ad_markers_valid else "NO", delta="Aligned" if ad_res.ad_markers_valid else "Misaligned")

        if ad_res.detected_splices:
            st.markdown("**Detected Splices:**")
            st.dataframe(ad_res.detected_splices, use_container_width=True)

        if ad_res.ad_insertion_issues:
            for iss in ad_res.ad_insertion_issues:
                st.error(f"❌ {iss}")
        else:
            st.success("✅ Ad splice points are fully closed and synchronized.")

# ----------------- TAB 3: QOE INCIDENT TRIAGER -----------------
with tab3:
    st.subheader("Tool: `query_stream_qoe`")
    st.caption("Ingests playback telemetry and executes automated Root Cause Analysis (RCA).")

    q1, q2 = st.columns(2)
    with q1:
        session_id = st.text_input("Session ID", "SESSION-US-EAST-49281")
        ttff = st.slider("Time to First Frame (ms)", min_value=500, max_value=8000, value=1800, step=100)
        rebuf = st.slider("Rebuffering Ratio (%)", min_value=0.0, max_value=8.0, value=0.2, step=0.1)
        cdn_pop = st.selectbox("CDN Edge POP", ["EWR-01 (New York)", "ORD-02 (Chicago)", "LAX-01 (Los Angeles)"])
        error_code = st.selectbox("Fatal Error Code", ["None", "CDN_504", "HTTP_503"])

        triage_btn = st.button("⚡ Execute `query_stream_qoe`", type="primary")

    with q2:
        if triage_btn:
            err = None if error_code == "None" else error_code
            qoe_res = server.query_stream_qoe(
                session_id=session_id,
                startup_time_ms=ttff,
                rebuffering_ratio_pct=rebuf,
                cdn_edge_pop=cdn_pop,
                error_code=err
            )

            if qoe_res.qoe_health_status == "HEALTHY":
                st.success(f"### Status: {qoe_res.qoe_health_status}")
            elif qoe_res.qoe_health_status == "DEGRADED":
                st.warning(f"### Status: {qoe_res.qoe_health_status}")
            else:
                st.error(f"### Status: {qoe_res.qoe_health_status}")

            st.markdown(f"**Root Cause Analysis:** {qoe_res.root_cause_analysis}")
            st.markdown(f"**Recommended Mitigation:** {qoe_res.recommended_mitigation}")

# ----------------- TAB 4: RAW MCP JSON-RPC SCHEMAS -----------------
with tab4:
    st.subheader("Official Anthropic Model Context Protocol (MCP) Tool Registry")
    st.markdown("These JSON-RPC schemas are exposed over stdio/HTTP to connected AI models (Claude, Cursor, LangChain).")
    st.json(server.list_tools())
