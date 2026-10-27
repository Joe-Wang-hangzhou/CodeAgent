import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

from agent import CodeAgent
from demo import DemoClient, make_response
from workflow import DocumentationWorkflow


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample_code.py"


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = Path(self.tmp.name) / "result"

    def run_flow(self, client=None, source=SAMPLE, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return DocumentationWorkflow(
                self.output, client=client or DemoClient(), mode="demo", **kwargs
            ).run(source)

    def test_end_to_end_with_source_read_and_shared_state(self):
        state = self.run_flow()
        self.assertEqual(state.status, "completed")
        self.assertEqual(state.revisions, 0)
        self.assertEqual(state.analysis["functions"][0]["name"], "calculate_sum")
        document = (self.output / "generated_document.md").read_text(encoding="utf-8")
        self.assertIn("read_file(path)", document)
        saved = json.loads((self.output / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["review"], {"approved": True, "issues": []})
        completed = [e["node"] for e in saved["events"] if e["status"] == "completed"]
        self.assertEqual(completed, ["analyst", "writer", "reviewer", "workflow"])

    def test_reviewer_feedback_reaches_writer(self):
        client = DemoClient(revision=True)
        state = self.run_flow(client)
        self.assertEqual(state.status, "completed")
        self.assertEqual(state.revisions, 1)
        self.assertEqual(client.review_count, 2)
        self.assertIn("## 已知问题", state.draft)

    def test_rejected_document_is_not_published(self):
        state = self.run_flow(DemoClient(reject_always=True))
        self.assertEqual(state.status, "failed")
        self.assertEqual(state.revisions, 1)
        self.assertIn("最大返工次数", state.error)
        self.assertFalse((self.output / "generated_document.md").exists())
        self.assertTrue((self.output / "draft.md").exists())
        self.assertFalse(state.review["approved"])

    def test_missing_file_persists_failure(self):
        state = self.run_flow(source=Path(self.tmp.name) / "missing.py")
        self.assertEqual(state.status, "failed")
        saved = json.loads((self.output / "state.json").read_text(encoding="utf-8"))
        self.assertIn("找不到源文件", saved["error"])
        self.assertFalse((self.output / "generated_document.md").exists())

    def test_failed_rerun_cannot_leave_previous_final_document(self):
        self.assertEqual(self.run_flow().status, "completed")
        state = self.run_flow(source=Path(self.tmp.name) / "missing.py")
        self.assertEqual(state.status, "failed")
        self.assertFalse((self.output / "generated_document.md").exists())

    def test_demo_does_not_pretend_to_analyze_other_code(self):
        other = Path(self.tmp.name) / "other.py"
        other.write_text("def other(): return 42\n", encoding="utf-8")
        state = self.run_flow(source=other)
        self.assertEqual(state.status, "failed")
        self.assertIn("离线演示仅适用于", state.error)

    def test_invalid_model_json_stops_workflow(self):
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=lambda **_: make_response("not json")
        )))
        state = self.run_flow(client)
        self.assertEqual(state.status, "failed")
        self.assertFalse(any(e["node"] == "writer" for e in state.events))

    def test_analysis_without_reading_source_is_rejected(self):
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=lambda **_: make_response(json.dumps({
                "summary": "guess", "functions": [], "usage": "guess", "issues": []
            }))
        )))
        state = self.run_flow(client)
        self.assertEqual(state.status, "failed")
        self.assertIn("未成功调用 read_file", state.error)

    def test_agent_loop_is_bounded(self):
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=lambda **_: make_response(tool_calls=[{
                "id": "loop", "type": "function",
                "function": {"name": "list_directory", "arguments": "{}"},
            }])
        )))
        with self.assertRaisesRegex(RuntimeError, "最大调用轮数 2"):
            CodeAgent("loop", client=client, use_tools=True, max_steps=2).chat("test")

    def test_cli_requires_key_in_live_mode(self):
        env = os.environ.copy()
        env["OPENAI_API_KEY"] = "your_qwen_api_key_here"
        result = subprocess.run(
            [sys.executable, str(ROOT / "main.py")], env=env,
            text=True, capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OPENAI_API_KEY", result.stderr)

    def test_live_cli_through_real_sdk_and_local_http_stub(self):
        try:
            import openai  # noqa: F401
        except ImportError:
            self.skipTest("安装 requirements.txt 后可验证真实 SDK")
        backend = DemoClient(revision=True)
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append((self.path, payload))
                message = backend.create(**payload).choices[0].message.model_dump()
                body = json.dumps({
                    "id": "local-test", "object": "chat.completion", "created": 0,
                    "model": "local-stub", "choices": [{"index": 0, "message": message,
                    "finish_reason": "tool_calls" if message.get("tool_calls") else "stop"}],
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            env = os.environ.copy()
            env.update(OPENAI_API_KEY="local-test-key",
                       OPENAI_BASE_URL=f"http://127.0.0.1:{server.server_port}/v1",
                       MODEL_NAME="local-stub", NO_PROXY="127.0.0.1,localhost")
            result = subprocess.run(
                [sys.executable, str(ROOT / "main.py"), str(SAMPLE), "--output", str(self.output)],
                env=env, text=True, capture_output=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)
        self.assertEqual(len(requests), 6)
        self.assertTrue(all(path == "/v1/chat/completions" for path, _ in requests))
        self.assertTrue(any(m["role"] == "tool" for m in requests[1][1]["messages"]))
        writer_payload = json.loads(requests[2][1]["messages"][1]["content"])
        self.assertEqual(writer_payload["analysis"]["functions"][1]["name"], "read_file")
        revised_payload = json.loads(requests[4][1]["messages"][1]["content"])
        self.assertFalse(revised_payload["review"]["approved"])
        self.assertTrue(revised_payload["review"]["issues"])
        state = json.loads((self.output / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["mode"], "live")
        self.assertEqual(state["revisions"], 1)


if __name__ == "__main__":
    unittest.main()
