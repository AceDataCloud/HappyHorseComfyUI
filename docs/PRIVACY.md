# Privacy

- Generation and editing nodes send prompts, public HTTPS reference media URLs, model choices, and the ComfyUI process's Ace Data Cloud key to `https://api.acedata.cloud/happyhorse/videos`.
- Task lookup sends existing task IDs to `https://api.acedata.cloud/happyhorse/tasks`; it does not create another generation.
- Load Video downloads completed video from an allowlisted Ace Data Cloud CDN into memory for ComfyUI's native `VIDEO` type.
- This package does not save the key in workflows or logs. Generation and editing may consume Ace Data Cloud Credits; check the current service price first.
