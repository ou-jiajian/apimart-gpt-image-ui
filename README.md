# APIMart GPT-Image-2 Web UI

一个本地运行的轻量级 Web UI，用来调用 APIMart 的 `gpt-image-2` 图像生成接口。

它适合不想手写 API 请求的人：打开浏览器，填入 API Key、提示词和参考图，就可以提交任务、查看轮询日志，并在出图后自动下载到本地。

## 功能

- 本地 Web 界面，直接在浏览器里操作
- 支持文生图和图生图
- 支持直接上传本地参考图
- 支持补充公网图片 URL 或 base64 图片数据
- 自动提交 APIMart 异步任务并轮询状态
- 支持本地任务队列，生成时也可以继续提交新任务
- 支持取消排队中或运行中的本地任务
- 轮询策略按 APIMart 文档做了保守调整
- 生成完成后自动保存到本地 `generated_images/`
- 如果本地等待超时，可以继续用 `task_id` 手动查询

## 环境要求

- Python 3.10+
- 一个可用的 APIMart API Key

## 安装

```bash
git clone <your-repo-url>
cd apimart-gpt-image-ui
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果你不想用虚拟环境，也可以直接安装 `requests` 后运行。

## 启动

```bash
python3 app.py
```

默认地址：

```text
http://127.0.0.1:8000
```

## 使用方法

1. 打开浏览器访问 `http://127.0.0.1:8000`
2. 输入 APIMart API Key
3. 填写提示词和图片比例
4. 如果需要图生图，直接上传本地参考图，或在文本框里填写图片 URL / base64
5. 点击“加入队列”
6. 等待任务完成，图片会自动保存到本地

生成任务会先进入本地队列。你可以连续提交多个提示词，右侧任务队列会显示每个任务的状态、日志和结果。

取消任务时：

- 排队中的任务会直接取消
- 运行中的任务会停止本地继续轮询
- 如果任务已经提交到 APIMart，远端任务可能仍会继续运行，后续可以用 `task_id` 手动查询

如果页面提示等待超时：

1. 复制返回的 `task_id`
2. 在页面下方“手动查询 Task ID”区域继续查询
3. 任务完成后仍会自动下载结果图

## 本地保存

生成结果默认保存到：

```text
generated_images/
```

这个目录已经加入 `.gitignore`，不会在默认情况下被提交到 GitHub。

## 已知说明

- 为了兼容部分本地 Python / SSL 环境问题，代码里对部分 HTTPS 错误做了兼容重试
- 当前单次固定生成 1 张图，和 APIMart 当前文档保持一致
- `size` 需要使用 APIMart 支持的比例格式，例如 `1:1`、`16:9`

## 项目结构

```text
.
├── app.py
├── README.md
├── requirements.txt
├── LICENSE
└── .gitignore
```

## License

MIT
