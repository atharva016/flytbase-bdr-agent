"""
FlytBase Outbound BDR AI Agent - Main Application
A multi-agent pipeline that automates outbound sales research and outreach.

Pipeline: Campaign Brief → Account Finder → Contact Hunter → Research Analyst → Email Composer

Built for FlytBase Hiring Hackathon 2026
Author: Atharva Jamdar
"""

import os
import json
import time
import threading
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS

from config import DEFAULT_CAMPAIGN_BRIEF, GEMINI_API_KEY
from llm_client import get_provider
from agents.account_finder import run_account_finder
from agents.contact_hunter import run_contact_hunter
from agents.research_analyst import run_research_analyst
from agents.email_composer import run_email_composer

# === Flask App Setup ===
app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# === Pipeline State (in-memory for demo) ===
pipeline_state = {
    "status": "idle",  # idle, running, complete, error
    "current_stage": 0,
    "stages": {
        1: {"name": "Account Identification", "status": "pending", "result": None},
        2: {"name": "Contact Discovery", "status": "pending", "result": None},
        3: {"name": "Account Research", "status": "pending", "result": None},
        4: {"name": "Email Generation", "status": "pending", "result": None},
    },
    "full_results": None,
    "error": None,
    "start_time": None,
    "end_time": None
}

# Global SSE clients list
sse_clients = []


def reset_pipeline_state():
    """Reset the pipeline state for a new run."""
    global pipeline_state
    pipeline_state = {
        "status": "idle",
        "current_stage": 0,
        "stages": {
            1: {"name": "Account Identification", "status": "pending", "result": None},
            2: {"name": "Contact Discovery", "status": "pending", "result": None},
            3: {"name": "Account Research", "status": "pending", "result": None},
            4: {"name": "Email Generation", "status": "pending", "result": None},
        },
        "full_results": None,
        "error": None,
        "start_time": None,
        "end_time": None
    }


def send_sse_event(event_type: str, data: dict):
    """Send a Server-Sent Event to all connected clients."""
    message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    dead_clients = []
    for client_queue in sse_clients:
        try:
            client_queue.append(message)
        except:
            dead_clients.append(client_queue)
    for dc in dead_clients:
        if dc in sse_clients:
            sse_clients.remove(dc)


def run_pipeline_async(brief: dict):
    """Run the full 4-stage pipeline in a background thread."""
    global pipeline_state
    
    try:
        get_provider()  # Validate LLM is configured
        
        pipeline_state["status"] = "running"
        pipeline_state["start_time"] = time.time()
        
        # === STAGE 1: Account Identification ===
        pipeline_state["current_stage"] = 1
        pipeline_state["stages"][1]["status"] = "running"
        send_sse_event("stage_update", {
            "stage": 1, "status": "running",
            "message": "Searching for mining companies in Latin America..."
        })
        
        accounts_result = run_account_finder(brief)
        pipeline_state["stages"][1]["status"] = "complete"
        pipeline_state["stages"][1]["result"] = accounts_result
        send_sse_event("stage_complete", {
            "stage": 1, "status": "complete",
            "result": accounts_result
        })
        
        accounts = accounts_result.get("accounts", [])
        if not accounts:
            raise ValueError("Stage 1 failed: No accounts found")
        
        # === STAGE 2: Contact Discovery ===
        pipeline_state["current_stage"] = 2
        pipeline_state["stages"][2]["status"] = "running"
        send_sse_event("stage_update", {
            "stage": 2, "status": "running",
            "message": f"Finding contacts at {len(accounts)} companies..."
        })
        
        contacts_result = run_contact_hunter(accounts)
        pipeline_state["stages"][2]["status"] = "complete"
        pipeline_state["stages"][2]["result"] = contacts_result
        send_sse_event("stage_complete", {
            "stage": 2, "status": "complete",
            "result": contacts_result
        })
        
        contacts = contacts_result.get("contacts", [])
        
        # === STAGE 3: Account Research ===
        pipeline_state["current_stage"] = 3
        pipeline_state["stages"][3]["status"] = "running"
        send_sse_event("stage_update", {
            "stage": 3, "status": "running",
            "message": f"Researching {len(accounts)} companies with real public data..."
        })
        
        research_result = run_research_analyst(accounts)
        pipeline_state["stages"][3]["status"] = "complete"
        pipeline_state["stages"][3]["result"] = research_result
        send_sse_event("stage_complete", {
            "stage": 3, "status": "complete",
            "result": research_result
        })
        
        research_briefs = research_result.get("research_briefs", [])
        
        # === STAGE 4: Email Generation ===
        pipeline_state["current_stage"] = 4
        pipeline_state["stages"][4]["status"] = "running"
        send_sse_event("stage_update", {
            "stage": 4, "status": "running",
            "message": f"Generating personalized emails for {len(contacts)} contacts..."
        })
        
        emails_result = run_email_composer(contacts, research_briefs, accounts)
        pipeline_state["stages"][4]["status"] = "complete"
        pipeline_state["stages"][4]["result"] = emails_result
        send_sse_event("stage_complete", {
            "stage": 4, "status": "complete",
            "result": emails_result
        })
        
        # === PIPELINE COMPLETE ===
        pipeline_state["status"] = "complete"
        pipeline_state["end_time"] = time.time()
        
        full_results = {
            "accounts": accounts_result,
            "contacts": contacts_result,
            "research": research_result,
            "emails": emails_result,
            "pipeline_metadata": {
                "duration_seconds": round(pipeline_state["end_time"] - pipeline_state["start_time"], 2),
                "total_accounts": len(accounts),
                "total_contacts": len(contacts),
                "total_research_briefs": len(research_briefs),
                "total_emails": len(emails_result.get("emails", [])),
                "status": "complete"
            }
        }
        
        pipeline_state["full_results"] = full_results
        send_sse_event("pipeline_complete", full_results)
        
        # Save results to file
        results_path = os.path.join(os.path.dirname(__file__), 'pipeline_results.json')
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(full_results, f, indent=2, ensure_ascii=False)
        print(f"\n[Pipeline] Results saved to {results_path}")
        print(f"[Pipeline] Completed in {full_results['pipeline_metadata']['duration_seconds']}s")
        
    except Exception as e:
        pipeline_state["status"] = "error"
        pipeline_state["error"] = str(e)
        send_sse_event("pipeline_error", {"error": str(e)})
        print(f"\n[Pipeline] ERROR: {e}")


# === API Routes ===

@app.route('/')
def index():
    """Serve the main dashboard."""
    return send_from_directory('static', 'index.html')


@app.route('/api/run-pipeline', methods=['POST'])
def run_pipeline():
    """Start the pipeline execution."""
    global pipeline_state
    
    if pipeline_state["status"] == "running":
        return jsonify({"error": "Pipeline is already running"}), 409
    
    # Get brief from request or use default
    data = request.get_json(silent=True) or {}
    brief = data.get("brief", DEFAULT_CAMPAIGN_BRIEF)
    
    # Reset state
    reset_pipeline_state()
    
    # Start pipeline in background thread
    thread = threading.Thread(target=run_pipeline_async, args=(brief,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "started",
        "message": "Pipeline execution started. Connect to /api/stream for real-time updates."
    })


@app.route('/api/stream')
def stream():
    """SSE endpoint for real-time pipeline updates."""
    def event_stream():
        client_queue = []
        sse_clients.append(client_queue)
        try:
            # Send initial state
            yield f"event: connected\ndata: {json.dumps({'status': pipeline_state['status']})}\n\n"
            
            while True:
                if client_queue:
                    message = client_queue.pop(0)
                    yield message
                else:
                    # Send heartbeat
                    yield f"event: heartbeat\ndata: {json.dumps({'time': time.time()})}\n\n"
                    time.sleep(1)
                
                # Stop streaming after pipeline completes
                if pipeline_state["status"] in ("complete", "error"):
                    # Drain remaining messages
                    while client_queue:
                        yield client_queue.pop(0)
                    break
        except GeneratorExit:
            pass
        finally:
            if client_queue in sse_clients:
                sse_clients.remove(client_queue)
    
    return Response(event_stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/status')
def get_status():
    """Get current pipeline status."""
    return jsonify({
        "status": pipeline_state["status"],
        "current_stage": pipeline_state["current_stage"],
        "stages": {
            str(k): {"name": v["name"], "status": v["status"]}
            for k, v in pipeline_state["stages"].items()
        },
        "error": pipeline_state.get("error")
    })


@app.route('/api/results')
def get_results():
    """Get pipeline results (if complete)."""
    if pipeline_state["status"] != "complete":
        return jsonify({"error": "Pipeline not complete yet", "status": pipeline_state["status"]}), 404
    
    return jsonify(pipeline_state["full_results"])


@app.route('/api/results/download')
def download_results():
    """Download results as JSON file."""
    if pipeline_state["full_results"]:
        return Response(
            json.dumps(pipeline_state["full_results"], indent=2, ensure_ascii=False),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=pipeline_results.json'}
        )
    return jsonify({"error": "No results available"}), 404


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "FlytBase Outbound BDR AI Agent"})


# === Main Entry Point ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 60)
    print("  FlytBase Outbound BDR AI Agent")
    print("  Autonomous Sales Intelligence Pipeline")
    print("=" * 60)
    
    try:
        provider = get_provider()
        print(f"\n✅ LLM configured using {provider}")
    except ValueError as e:
        print(f"\n⚠️  WARNING: {e}")
        print("  Please set GEMINI_API_KEY or GROQ_API_KEY as an environment variable")
        print("  Or add it to the .env file\n")
    
    print(f"\n🚀 Starting server on http://localhost:{port}")
    print(f"📊 Dashboard: http://localhost:{port}/")
    print(f"📡 API: http://localhost:{port}/api/run-pipeline")
    print(f"💓 Health: http://localhost:{port}/health\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
