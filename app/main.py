from flask import Flask, request, Response, stream_with_context, make_response
from flask_cors import CORS
import functions  # client & assistant_id are exposed here

app = Flask(__name__)
CORS(app)

client = functions.client
assistant_id = functions.assistant_id

def run_stream(thread_id: str):
    """Yield assistant text deltas for streaming."""
    stream = client.beta.threads.runs.create(
        thread_id=thread_id, assistant_id=assistant_id, stream=True
    )
    for chunk in stream:
        if hasattr(chunk.data, "content") and chunk.data.content:
            if chunk.data.role == "assistant":
                yield chunk.data.content[0].text.value

@app.route("/", methods=["GET"])
@app.route("/start", methods=["GET"])
def index():
    return (
        "✅ Singapore-Way AI is running.\n"
        "POST JSON {\"message\": \"…\"} to /chat (stream) or /chat_sync.",
        200,
        {"Content-Type": "text/plain; charset=utf-8"},
    )

@app.route("/chat", methods=["POST"])
def chat_stream():
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return (
            "ERROR 400 – POST body must be JSON: {\"message\": \"your question\"}",
            400,
            {"Content-Type": "text/plain; charset=utf-8"},
        )
    user_msg = data["message"]

    # create thread & post user message
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_msg
    )

    # stream back assistant deltas
    resp = Response(
        stream_with_context(run_stream(thread.id)),
        mimetype="text/plain",
    )
    resp.headers["X-Thread-Id"] = thread.id
    return resp

@app.route("/chat_sync", methods=["POST"])
def chat_sync():
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return (
            "ERROR 400 – POST body must be JSON: {\"message\": \"your question\"}",
            400,
            {"Content-Type": "text/plain; charset=utf-8"},
        )
    user_msg = data["message"]

    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_msg
    )

    # blocking run
    client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant_id
    )
    final = client.beta.threads.messages.list(thread_id=thread.id).data[0]

    resp = make_response(final.content[0].text.value, 200)
    resp.headers["Content-Type"] = "text/plain; charset=utf-8"
    resp.headers["X-Thread-Id"] = thread.id
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
