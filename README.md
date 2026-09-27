# 📡 StreamingTelemetry-MCP: Model Context Protocol Server

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Protocol](https://img.shields.io/badge/Protocol-Anthropic_MCP_2024--11--05-blueviolet?style=flat)
![UI](https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Domain](https://img.shields.io/badge/Domain-Video_Streaming_%26_QoE-blue)

> An open-source **Model Context Protocol (MCP)** server providing AI coding agents (Claude Desktop, Cursor, LangChain) with direct tools to inspect HLS video manifests, audit SCTE-35 ad break splices, and triage playback QoE incidents.

---

## 📌 The Problem: LLMs Lack Streaming Diagnostics

Autonomous agents and LLMs are excellent at writing general code, but lack real-time visibility into video delivery systems:
1. **Manifest Blindness:** Standard coding assistants cannot parse `.m3u8` playlists to detect ladder step jumps (> 2.5x) or segment duration overruns.
2. **SSAI Splicing Failures:** Unsynchronized SCTE-35 ad break markers cause client playback freezing and lost ad impressions.
3. **Slow Incident Triage:** Correlating player telemetry (rebuffering ratio, time-to-first-frame, edge POP failures) across fragmented client devices takes engineers hours.

---

## 💡 The Solution: Streaming Diagnostic Tools via MCP

**StreamingTelemetry-MCP** bridges AI assistants directly to video engineering pipelines via standard **JSON-RPC 2.0** tool definitions:

```mermaid
flowchart TD
    A[AI Assistant / Agent: Claude / Cursor] -->|JSON-RPC 2.0: tools/call| B[StreamingTelemetry-MCP Server]
    
    subgraph Exposed Diagnostic Tools
        B --> C[Tool 1: inspect_hls_manifest]
        B --> D[Tool 2: validate_ad_markers]
        B --> E[Tool 3: query_stream_qoe]
    end
    
    C --> F[Bitrate Ladder & Target Duration Audit]
    D --> G[SCTE-35 / DATERANGE Splice Verification]
    E --> H[Automated Root Cause Analysis & Traffic Steering]
