#!/usr/bin/env python3
import json
import os
import re
import ssl
import time
import warnings
import urllib.error
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning


HOST = "127.0.0.1"
PORT = 8000
APIMART_BASE_URL = "https://api.apimart.ai"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_images")
INITIAL_POLL_DELAY_SECONDS = 12
POLL_INTERVAL_SECONDS = 5
MAX_WAIT_SECONDS = 600

warnings.simplefilter("ignore", InsecureRequestWarning)


INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>APIMart GPT-Image-2 控制台</title>
  <style>
    :root {
      --bg: #f7f3ea;
      --panel: rgba(255, 252, 245, 0.86);
      --panel-strong: #fffaf0;
      --ink: #1f1a17;
      --muted: #74675f;
      --line: rgba(102, 78, 53, 0.18);
      --accent: #bd5d38;
      --accent-strong: #8f3d20;
      --success: #236c4d;
      --danger: #9c2f2f;
      --shadow: 0 18px 60px rgba(69, 43, 24, 0.13);
      --radius: 24px;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      color: var(--ink);
      font-family: "Avenir Next", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(233, 180, 111, 0.30), transparent 32%),
        radial-gradient(circle at top right, rgba(173, 106, 66, 0.22), transparent 28%),
        linear-gradient(135deg, #f8efe2, #f6f3ee 58%, #eee5d7);
      min-height: 100vh;
    }

    .shell {
      width: min(1120px, calc(100vw - 32px));
      margin: 24px auto;
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 20px;
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }

    .left {
      padding: 28px;
    }

    .right {
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    .hero {
      margin-bottom: 24px;
    }

    .eyebrow {
      display: inline-block;
      padding: 6px 12px;
      border-radius: 999px;
      background: rgba(189, 93, 56, 0.10);
      color: var(--accent-strong);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 14px;
    }

    h1 {
      margin: 0 0 10px;
      font-size: clamp(30px, 5vw, 52px);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }

    .subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.65;
      max-width: 60ch;
    }

    form {
      display: grid;
      gap: 16px;
    }

    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    label {
      display: block;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 8px;
    }

    input, textarea, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px 16px;
      background: rgba(255, 255, 255, 0.72);
      color: var(--ink);
      font: inherit;
      outline: none;
      transition: border-color 160ms ease, transform 160ms ease, background 160ms ease;
    }

    input:focus, textarea:focus, select:focus {
      border-color: rgba(189, 93, 56, 0.6);
      background: #fff;
      transform: translateY(-1px);
    }

    textarea {
      min-height: 132px;
      resize: vertical;
    }

    .hint {
      margin-top: 6px;
      font-size: 12px;
      color: var(--muted);
    }

    .actions {
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
      padding-top: 6px;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 14px 22px;
      background: linear-gradient(135deg, var(--accent), var(--accent-strong));
      color: white;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 12px 28px rgba(143, 61, 32, 0.24);
      transition: transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease;
    }

    button:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 16px 30px rgba(143, 61, 32, 0.26);
    }

    button:disabled {
      cursor: wait;
      opacity: 0.72;
    }

    .ghost {
      background: transparent;
      color: var(--accent-strong);
      border: 1px solid rgba(189, 93, 56, 0.22);
      box-shadow: none;
    }

    .panel-title {
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin: 0 0 14px;
    }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(35, 108, 77, 0.12);
      color: var(--success);
      font-weight: 700;
      font-size: 14px;
    }

    .status-badge.error {
      background: rgba(156, 47, 47, 0.10);
      color: var(--danger);
    }

    .status-badge.waiting {
      background: rgba(189, 93, 56, 0.10);
      color: var(--accent-strong);
    }

    .log {
      margin: 0;
      padding: 16px;
      min-height: 170px;
      max-height: 300px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(44, 31, 23, 0.95);
      color: #f7efe4;
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 13px;
      line-height: 1.65;
      white-space: pre-wrap;
    }

    .image-frame {
      border-radius: 22px;
      overflow: hidden;
      border: 1px solid var(--line);
      background:
        linear-gradient(135deg, rgba(255,255,255,0.76), rgba(245, 231, 211, 0.92));
      min-height: 320px;
      display: grid;
      place-items: center;
      position: relative;
    }

    .image-frame img {
      display: block;
      width: 100%;
      height: auto;
    }

    .placeholder {
      padding: 28px;
      text-align: center;
      color: var(--muted);
      line-height: 1.7;
    }

    .meta {
      display: grid;
      gap: 12px;
    }

    .file-list {
      margin-top: 10px;
      display: grid;
      gap: 8px;
    }

    .file-chip {
      padding: 10px 12px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.66);
      font-size: 13px;
      color: var(--ink);
      line-height: 1.5;
    }

    .divider {
      height: 1px;
      background: var(--line);
      margin: 6px 0 2px;
    }

    .meta-item {
      padding: 14px 16px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.58);
      border: 1px solid var(--line);
    }

    .meta-key {
      display: block;
      margin-bottom: 4px;
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .meta-value {
      word-break: break-all;
      font-size: 14px;
      line-height: 1.6;
    }

    a {
      color: var(--accent-strong);
    }

    @media (max-width: 900px) {
      .shell {
        grid-template-columns: 1fr;
      }

      .grid {
        grid-template-columns: 1fr;
      }

      .left, .right {
        padding: 20px;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="card left">
      <div class="hero">
        <div class="eyebrow">Local Web UI</div>
        <h1>APIMart GPT-Image-2</h1>
        <p class="subtitle">在这个页面里直接填 APIMart 的 API Key 和提示词，后端会替你提交异步任务、自动轮询结果，并把最终图片展示出来。</p>
      </div>

      <form id="generate-form">
        <div>
          <label for="apiKey">API Key</label>
          <input id="apiKey" name="apiKey" type="password" placeholder="填入 APIMart API Key">
          <div class="hint">只在当前浏览器会话里使用，不会写入磁盘。</div>
        </div>

        <div>
          <label for="prompt">Prompt</label>
          <textarea id="prompt" name="prompt" placeholder="例如：一只橘猫坐在窗台上看夕阳，电影感，水彩插画风格"></textarea>
        </div>

        <div class="grid">
          <div>
            <label for="size">图片比例</label>
            <select id="size" name="size">
              <option value="1:1">1:1</option>
              <option value="16:9">16:9</option>
              <option value="9:16">9:16</option>
              <option value="4:3">4:3</option>
              <option value="3:4">3:4</option>
              <option value="3:2">3:2</option>
              <option value="2:3">2:3</option>
              <option value="5:4">5:4</option>
              <option value="4:5">4:5</option>
              <option value="2:1">2:1</option>
              <option value="1:2">1:2</option>
              <option value="21:9">21:9</option>
              <option value="9:21">9:21</option>
            </select>
          </div>

          <div>
            <label for="officialFallback">官方渠道兜底</label>
            <select id="officialFallback" name="officialFallback">
              <option value="false">false</option>
              <option value="true">true</option>
            </select>
          </div>
        </div>

        <div>
          <label for="imageFiles">参考图上传（可选）</label>
          <input id="imageFiles" name="imageFiles" type="file" accept="image/*" multiple>
          <div class="hint">直接选择本地图片即可，页面会自动转成平台支持的格式，最多 16 张。</div>
          <div id="fileList" class="file-list"></div>
        </div>

        <div>
          <label for="imageUrls">参考图链接 / Base64（可选补充）</label>
          <textarea id="imageUrls" name="imageUrls" placeholder="每行一条 URL 或 data:image/...;base64,..."></textarea>
          <div class="hint">你也可以额外手填公网图片链接或 base64。上传文件和这里的内容会合并提交。</div>
        </div>

        <div class="actions">
          <button id="submitBtn" type="submit">开始生成</button>
          <button id="fillDemoBtn" class="ghost" type="button">填入示例</button>
        </div>
      </form>

      <div class="divider"></div>

      <form id="lookup-form">
        <div>
          <label for="lookupTaskId">手动查询 Task ID</label>
          <input id="lookupTaskId" name="lookupTaskId" type="text" placeholder="例如：task_01KPQ7J7DWB7QZ3WCEK3YVPBRA">
          <div class="hint">如果生成时提示超时，可以把返回的 task_id 粘到这里继续查。</div>
        </div>

        <div class="actions">
          <button id="lookupBtn" type="submit">查询任务</button>
        </div>
      </form>
    </section>

    <aside class="card right">
      <div>
        <p class="panel-title">任务状态</p>
        <div id="statusBadge" class="status-badge waiting">等待提交</div>
      </div>

      <div>
        <p class="panel-title">运行日志</p>
        <pre id="logBox" class="log">准备就绪，填写参数后点击“开始生成”。</pre>
      </div>

      <div>
        <p class="panel-title">生成结果</p>
        <div id="imageFrame" class="image-frame">
          <div class="placeholder">图片生成完成后会显示在这里。</div>
        </div>
      </div>

      <div class="meta">
        <div class="meta-item">
          <span class="meta-key">Task ID</span>
          <div id="taskId" class="meta-value">-</div>
        </div>
        <div class="meta-item">
          <span class="meta-key">图片链接</span>
          <div id="imageUrl" class="meta-value">-</div>
        </div>
      </div>
    </aside>
  </main>

  <script>
    const form = document.getElementById("generate-form");
    const submitBtn = document.getElementById("submitBtn");
    const lookupForm = document.getElementById("lookup-form");
    const lookupBtn = document.getElementById("lookupBtn");
    const fillDemoBtn = document.getElementById("fillDemoBtn");
    const imageFilesInput = document.getElementById("imageFiles");
    const statusBadge = document.getElementById("statusBadge");
    const logBox = document.getElementById("logBox");
    const imageFrame = document.getElementById("imageFrame");
    const taskIdNode = document.getElementById("taskId");
    const imageUrlNode = document.getElementById("imageUrl");
    const fileListNode = document.getElementById("fileList");
    let uploadedImageDataUrls = [];

    function setStatus(text, kind) {
      statusBadge.textContent = text;
      statusBadge.className = "status-badge" + (kind ? " " + kind : "");
    }

    function setLog(lines) {
      logBox.textContent = lines.join("\\n");
      logBox.scrollTop = logBox.scrollHeight;
    }

    function setImage(url) {
      if (!url) {
        imageFrame.innerHTML = '<div class="placeholder">图片生成完成后会显示在这里。</div>';
        imageUrlNode.textContent = "-";
        return;
      }
      imageFrame.innerHTML = '<img alt="生成结果" src="' + url + '">';
      imageUrlNode.innerHTML = '<a href="' + url + '" target="_blank" rel="noreferrer">' + url + '</a>';
    }

    function renderFileList(files) {
      if (!files.length) {
        fileListNode.innerHTML = "";
        return;
      }
      fileListNode.innerHTML = files
        .map(file => '<div class="file-chip">' + file.name + ' (' + Math.max(1, Math.round(file.size / 1024)) + ' KB)</div>')
        .join("");
    }

    function readFileAsDataUrl(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error("读取参考图失败: " + file.name));
        reader.readAsDataURL(file);
      });
    }

    imageFilesInput.addEventListener("change", async () => {
      const files = Array.from(imageFilesInput.files || []);
      renderFileList(files);

      if (files.length > 16) {
        uploadedImageDataUrls = [];
        setStatus("参考图过多", "error");
        setLog(["最多只能上传 16 张参考图。"]);
        return;
      }

      try {
        uploadedImageDataUrls = await Promise.all(files.map(readFileAsDataUrl));
        if (files.length) {
          setStatus("参考图已就绪", "waiting");
          setLog(["已读取本地参考图，可直接开始生成。"]);
        }
      } catch (error) {
        uploadedImageDataUrls = [];
        setStatus("参考图读取失败", "error");
        setLog([String(error.message || error)]);
      }
    });

    fillDemoBtn.addEventListener("click", () => {
      document.getElementById("prompt").value = "一只橘猫坐在窗台上看夕阳，电影感，水彩插画风格，细节丰富，暖色调";
      document.getElementById("size").value = "16:9";
      document.getElementById("officialFallback").value = "false";
      document.getElementById("imageUrls").value = "";
      imageFilesInput.value = "";
      uploadedImageDataUrls = [];
      renderFileList([]);
    });

    async function handleTaskResult(result) {
      taskIdNode.textContent = result.task_id || "-";
      setLog(result.logs || ["任务查询完成。"]);
      setImage(result.image_url || "");
      if (result.saved_path) {
        imageUrlNode.innerHTML += '<br><br><strong>本地保存:</strong><br>' + result.saved_path;
      }
      if (result.image_url) {
        setStatus("生成完成", "");
      } else {
        setStatus("任务未完成", "waiting");
      }
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      const apiKey = document.getElementById("apiKey").value.trim();
      const prompt = document.getElementById("prompt").value.trim();
      const size = document.getElementById("size").value;
      const officialFallback = document.getElementById("officialFallback").value === "true";
      const imageUrls = document.getElementById("imageUrls").value
        .split("\\n")
        .map(line => line.trim())
        .filter(Boolean);
      const allImageUrls = uploadedImageDataUrls.concat(imageUrls);

      if (!apiKey) {
        setStatus("缺少 API Key", "error");
        setLog(["请先填写 APIMart API Key。"]);
        return;
      }

      if (!prompt) {
        setStatus("缺少 Prompt", "error");
        setLog(["请先填写 Prompt。"]);
        return;
      }

      if (allImageUrls.length > 16) {
        setStatus("参考图过多", "error");
        setLog(["上传图片和文本框里的参考图总数不能超过 16 张。"]);
        return;
      }

      submitBtn.disabled = true;
      taskIdNode.textContent = "-";
      setImage("");
      setStatus("提交中", "waiting");
      setLog(["正在提交任务..."]);

      try {
        const response = await fetch("/api/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            api_key: apiKey,
            prompt,
            size,
            official_fallback: officialFallback,
            image_urls: allImageUrls
          })
        });

        const result = await response.json();

        if (!response.ok) {
          throw new Error(result.error || "请求失败");
        }

        await handleTaskResult(result);
      } catch (error) {
        setStatus("请求失败", "error");
        setLog([String(error.message || error)]);
      } finally {
        submitBtn.disabled = false;
      }
    });

    lookupForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const apiKey = document.getElementById("apiKey").value.trim();
      const taskId = document.getElementById("lookupTaskId").value.trim();

      if (!apiKey) {
        setStatus("缺少 API Key", "error");
        setLog(["请先填写 APIMart API Key。"]);
        return;
      }

      if (!taskId) {
        setStatus("缺少 Task ID", "error");
        setLog(["请先填写要查询的 task_id。"]);
        return;
      }

      lookupBtn.disabled = true;
      taskIdNode.textContent = taskId;
      setStatus("查询中", "waiting");
      setLog(["正在查询任务状态..."]);

      try {
        const response = await fetch("/api/task-status", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            api_key: apiKey,
            task_id: taskId
          })
        });

        const result = await response.json();

        if (!response.ok) {
          throw new Error(result.error || "查询失败");
        }

        await handleTaskResult(result);
      } catch (error) {
        setStatus("查询失败", "error");
        setLog([String(error.message || error)]);
      } finally {
        lookupBtn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


def json_response(handler, status_code, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    try:
        handler.send_response(status_code)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
        # The browser may close a long-running request after refresh/navigation.
        # The task may still be running on APIMart, so this is safe to ignore.
        return


def should_retry_with_insecure_ssl(error):
    text = str(error)
    return (
        isinstance(getattr(error, "__cause__", None), ssl.SSLCertVerificationError)
        or "CERTIFICATE_VERIFY_FAILED" in text
        or "EOF occurred in violation of protocol" in text
        or "SSLEOFError" in text
    )


def request_with_ssl_fallback(method, url, timeout, retries=1, retry_delay=1.0, **kwargs):
    last_error = None
    for attempt in range(retries + 1):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.SSLError as error:
            last_error = error
            if should_retry_with_insecure_ssl(error):
                retry_kwargs = dict(kwargs)
                retry_kwargs["verify"] = False
                try:
                    response = requests.request(method, url, timeout=timeout, **retry_kwargs)
                    response.raise_for_status()
                    return response
                except Exception as retry_error:
                    last_error = retry_error
            if attempt < retries:
                time.sleep(retry_delay)
                continue
            raise last_error
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
            last_error = error
            if attempt < retries:
                time.sleep(retry_delay)
                continue
            raise
    raise last_error


def http_json_request(method, url, api_key, payload=None):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = request_with_ssl_fallback(
        method,
        url,
        timeout=90,
        headers=headers,
        json=payload,
    )
    return response.json()


def fetch_task_status(task_id, api_key, retries=2):
    encoded_task_id = urllib.parse.quote(task_id, safe="")
    url = f"{APIMART_BASE_URL}/v1/tasks/{encoded_task_id}?language=zh"
    return http_json_request("GET", url, api_key, payload=None)


def extract_image_url(task_result):
    images = task_result.get("data", {}).get("result", {}).get("images", [])
    if not images:
        return None
    url_value = images[0].get("url")
    if isinstance(url_value, list) and url_value:
        return url_value[0]
    if isinstance(url_value, str):
        return url_value
    return None


def build_task_status_response(task_id, task_result, logs, prompt_for_save="task_lookup"):
    task_data = task_result.get("data", {})
    image_url = extract_image_url(task_result)
    saved_path = None

    if task_data.get("status") == "completed" and image_url:
        try:
            saved_path = download_image_to_local(image_url, prompt_for_save, task_id)
            logs.append(f"图片已自动保存到本地: {saved_path}")
        except Exception as error:
            logs.append(f"自动保存到本地失败: {error}")

    return {
        "task_id": task_id,
        "status": task_data.get("status", "unknown"),
        "progress": task_data.get("progress", 0),
        "image_url": image_url,
        "saved_path": saved_path,
        "logs": logs,
        "raw": task_result,
    }


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def slugify_prompt(prompt):
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", prompt).strip("_")
    return slug[:40] or "image"


def guess_extension(image_url, content_type):
    if content_type:
        lowered = content_type.lower()
        if "png" in lowered:
            return ".png"
        if "jpeg" in lowered or "jpg" in lowered:
            return ".jpg"
        if "webp" in lowered:
            return ".webp"
        if "gif" in lowered:
            return ".gif"
    path = urllib.parse.urlparse(image_url).path.lower()
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        if path.endswith(ext):
            return ext
    return ".png"


def download_image_to_local(image_url, prompt, task_id):
    ensure_output_dir()
    response = request_with_ssl_fallback("GET", image_url, timeout=120)
    content_type = response.headers.get("Content-Type", "")
    image_bytes = response.content

    ext = guess_extension(image_url, content_type)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{slugify_prompt(prompt)}-{task_id[-8:]}{ext}"
    file_path = os.path.join(OUTPUT_DIR, filename)

    with open(file_path, "wb") as file_obj:
        file_obj.write(image_bytes)

    return file_path


def extract_error_body(error):
    if isinstance(error, requests.exceptions.HTTPError):
        response = error.response
        try:
            parsed = response.json()
        except Exception:
            parsed = response.text
        return {
            "http_status": response.status_code,
            "response": parsed,
        }

    if not isinstance(error, urllib.error.HTTPError):
        return str(error)
    try:
        body = error.read().decode("utf-8")
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            return {
                "http_status": error.code,
                "response": parsed,
            }
        return body
    except Exception:
        return {
            "http_status": error.code,
            "response": str(error),
        }


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = INDEX_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        json_response(self, 404, {"error": "Not found"})

    def do_POST(self):
        if self.path not in ("/api/generate", "/api/task-status"):
            json_response(self, 404, {"error": "Not found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            body = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            json_response(self, 400, {"error": "请求体不是合法 JSON"})
            return

        if self.path == "/api/task-status":
            api_key = str(body.get("api_key", "")).strip()
            task_id = str(body.get("task_id", "")).strip()

            if not api_key:
                json_response(self, 400, {"error": "缺少 api_key"})
                return

            if not task_id:
                json_response(self, 400, {"error": "缺少 task_id"})
                return

            logs = [f"开始手动查询任务: {task_id}"]

            try:
                task_result = fetch_task_status(task_id, api_key)
            except Exception as error:
                json_response(
                    self,
                    502,
                    {"error": f"查询任务状态失败: {extract_error_body(error)}", "task_id": task_id, "logs": logs},
                )
                return

            task_data = task_result.get("data", {})
            logs.append(f"当前状态: status={task_data.get('status', 'unknown')}, progress={task_data.get('progress', 0)}")
            json_response(self, 200, build_task_status_response(task_id, task_result, logs))
            return

        api_key = str(body.get("api_key", "")).strip()
        prompt = str(body.get("prompt", "")).strip()
        size = str(body.get("size", "1:1")).strip() or "1:1"
        official_fallback = bool(body.get("official_fallback", False))
        image_urls = body.get("image_urls", [])

        if not api_key:
            json_response(self, 400, {"error": "缺少 api_key"})
            return

        if not prompt:
            json_response(self, 400, {"error": "缺少 prompt"})
            return

        if not isinstance(image_urls, list):
            json_response(self, 400, {"error": "image_urls 必须是数组"})
            return

        cleaned_image_urls = [str(item).strip() for item in image_urls if str(item).strip()]
        if len(cleaned_image_urls) > 16:
            json_response(self, 400, {"error": "参考图最多 16 张"})
            return

        payload = {
            "model": "gpt-image-2",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "official_fallback": official_fallback,
        }
        if cleaned_image_urls:
            payload["image_urls"] = cleaned_image_urls

        logs = [
            "准备提交到 APIMart...",
            f"size={size}",
            f"official_fallback={str(official_fallback).lower()}",
            f"reference_images={len(cleaned_image_urls)}",
        ]

        try:
            submit_result = http_json_request(
                "POST",
                f"{APIMART_BASE_URL}/v1/images/generations",
                api_key,
                payload=payload,
            )
        except Exception as error:
            json_response(
                self,
                502,
                {"error": f"提交任务失败: {extract_error_body(error)}"},
            )
            return

        task_id = (
            submit_result.get("data", [{}])[0].get("task_id")
            if isinstance(submit_result.get("data"), list) and submit_result.get("data")
            else None
        )

        if not task_id:
            json_response(
                self,
                502,
                {"error": f"未从提交结果中拿到 task_id: {submit_result}"},
            )
            return

        logs.append(f"任务已提交，task_id={task_id}")
        logs.append(f"按 APIMart 建议，先等待 {INITIAL_POLL_DELAY_SECONDS} 秒再开始首次查询。")
        time.sleep(INITIAL_POLL_DELAY_SECONDS)

        deadline = time.time() + MAX_WAIT_SECONDS
        task_result = None

        while time.time() < deadline:
            try:
                task_result = fetch_task_status(task_id, api_key)
            except Exception as error:
                logs.append(f"任务状态查询异常，准备重试: {extract_error_body(error)}")
                transient_recovered = False
                for retry_index in range(3):
                    try:
                        time.sleep(2 + retry_index)
                        task_result = fetch_task_status(task_id, api_key)
                        logs.append(f"任务状态查询重试成功，第 {retry_index + 1} 次恢复。")
                        transient_recovered = True
                        break
                    except Exception as retry_error:
                        logs.append(f"任务状态查询重试失败，第 {retry_index + 1} 次: {extract_error_body(retry_error)}")
                if not transient_recovered:
                    json_response(
                        self,
                        502,
                        {"error": f"查询任务状态失败: {extract_error_body(error)}", "task_id": task_id, "logs": logs},
                    )
                    return

            task_data = task_result.get("data", {})
            status = task_data.get("status", "unknown")
            progress = task_data.get("progress", 0)
            logs.append(f"轮询状态: status={status}, progress={progress}")

            if status == "completed":
                break

            if status == "failed":
                error_info = task_data.get("error", {})
                json_response(
                    self,
                    502,
                    {
                        "error": f"任务失败: {error_info}",
                        "task_id": task_id,
                        "logs": logs,
                    },
                )
                return

            if status == "cancelled":
                json_response(
                    self,
                    502,
                    {"error": "任务已被取消", "task_id": task_id, "logs": logs},
                )
                return

            time.sleep(POLL_INTERVAL_SECONDS)
        else:
            json_response(
                self,
                504,
                {
                    "error": "等待任务完成超时，请稍后用 task_id 手动查询",
                    "task_id": task_id,
                    "logs": logs + [
                        f"本地等待上限为 {MAX_WAIT_SECONDS} 秒，页面下方“手动查询 Task ID”可继续查询。",
                    ],
                },
            )
            return
        logs.append("任务完成，已拿到图片链接。")

        json_response(
            self,
            200,
            build_task_status_response(task_id, task_result, logs, prompt_for_save=prompt),
        )

    def log_message(self, format, *args):
        return


def main():
    port = int(os.environ.get("PORT", PORT))
    server = ThreadingHTTPServer((HOST, port), AppHandler)
    print(f"Server running at http://{HOST}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
