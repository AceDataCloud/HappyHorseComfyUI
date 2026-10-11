# Happy Horse for ComfyUI by Ace Data Cloud

Generate and edit Happy Horse videos with your Ace Data Cloud account, retrieve the **same task ID**, and load completed results as ComfyUI's native `VIDEO` type. These nodes call a hosted API; no local model or GPU is needed. Submissions consume Credits at the [current Happy Horse price](https://platform.acedata.cloud/models).

[简体中文](docs/README.zh-CN.md) · [Ace Data Cloud](https://platform.acedata.cloud) · [Issues](https://github.com/AceDataCloud/HappyHorseComfyUI/issues)

| Node | Dify action and model family |
| --- | --- |
| **Happy Horse Text to Video** | `generate`; 1.0 and 1.1 T2V |
| **Happy Horse Image to Video** | `image_to_video`; 1.0 and 1.1 I2V |
| **Happy Horse Reference to Video** | `reference_to_video`; 1.0 and 1.1 R2V |
| **Happy Horse Video Edit** | `video_edit`; `happyhorse-1.0-video-edit` |
| **Happy Horse Retrieve Task / Retrieve Tasks** | Query one or many existing task IDs |
| **Happy Horse Load Video** | Decode a completed Ace media URL into native `VIDEO` |

All **seven model IDs** and all four generation actions in [HappyHorseDify](https://github.com/AceDataCloud/HappyHorseDify) are offered, with model choices kept within their supported action. Model availability and pricing may differ by version and resolution.

## Install

Once the Registry version is active, open **ComfyUI-Manager → Custom Nodes**, search **Happy Horse**, confirm publisher **acedatacloud** and package **Happy Horse by Ace Data Cloud**, install, and restart. The Registry ID is `happy-horse`; the source repository is `AceDataCloud/HappyHorseComfyUI`. Source availability and Registry upload alone do not prove Manager installation.

For local source testing:

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/AceDataCloud/HappyHorseComfyUI.git
cd HappyHorseComfyUI
python -m pip install -r requirements.txt
```

This package targets ComfyUI 0.39.0 or newer because Load Video uses its native `VIDEO` type. Restart and search for **Happy Horse**.

## Set your Ace Data Cloud key

Use an application key with Happy Horse access. Set it in the **ComfyUI process environment** and restart:

```bash
export ACEDATACLOUD_API_KEY='paste-your-key-here'
python main.py --cpu
```

`ACEDATACLOUD_API_TOKEN` is also accepted. Keep the key out of workflows, screenshots, issues, and the repository. If you restrict API paths, allow `/happyhorse/videos` and `/happyhorse/tasks`.

## Generate and retrieve

Import [01-submit-text-to-video.json](examples/01-submit-text-to-video.json) with **File → Open**, select the model and price, then run **once**. Copy the task ID displayed by Preview as Text. A submitted task is not a completed video. If submission times out without an ID, inspect Ace request history before paying for another submission.

For I2V, enter one public HTTPS first-frame URL. For R2V, enter a JSON array or one URL per line with 1–9 references. For video edit, enter a public HTTPS video URL and optionally 0–5 reference images; `origin` preserves source audio. Each action only offers its compatible model IDs. T2V and R2V use the selected ratio; I2V follows the first-frame image ratio. Video edit duration follows the input video.

Import [02-retrieve-and-save.json](examples/02-retrieve-and-save.json), replace its placeholder task ID, then run. It connects **Retrieve Task → Load Video → Save Video**. Retrieve waits up to 240 seconds for the **same task**. If it remains pending, rerun only this retrieval workflow. The `VIDEO` output also connects to other native ComfyUI video nodes.

The read-only Retrieve Tasks node accepts a JSON array of 1–20 IDs and returns a compact JSON status list. It never submits a new video.

## Check usage and troubleshoot

Check the submission by task or trace ID in the [Ace Data Cloud Console](https://platform.acedata.cloud/console/applications). Read-only queries and media downloads should not create another generation.

| Symptom | Action |
| --- | --- |
| Key missing or HTTP 401/403 | Check the key in the running ComfyUI process and Happy Horse access. |
| HTTP 429 | Wait for the service limit; keep any accepted task ID. |
| Pending | Query the same task ID again; do not rerun a paid submit node. |
| Submission timeout or HTTP 5xx | Inspect request history before resubmitting. |
| Video download error | Confirm terminal success and an Ace CDN URL. |

Prompts and reference media URLs are sent to `api.acedata.cloud`; completed videos are downloaded from Ace CDN. See [privacy notes](docs/PRIVACY.md). Only submit content you have permission to process.

## Development

```bash
python -m unittest discover -s tests -v
python -m py_compile __init__.py client.py nodes.py
```

`pyproject.toml` declares short Registry ID `happy-horse`, publisher `acedatacloud`, and a 400×400 proportional resize of the [canonical Ace logo](https://cdn.acedata.cloud/assets/logo.png).
