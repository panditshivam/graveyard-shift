FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
USER user
ENV PATH=/home/user/.local/bin:$PATH HF_HOME=/home/user/.cache/huggingface PYTHONUNBUFFERED=1
WORKDIR /home/user/app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir transformers==4.57.1
COPY --chown=user . .
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-Coder-0.5B-Instruct',revision='ea3f2471cf1b1f0db85067f1ef93848e38e88c25',allow_patterns=['*.json','*.safetensors','*.txt','*.model'])"
EXPOSE 7860
CMD ["python", "server.py"]
