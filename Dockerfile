FROM codex-universal:fixed

WORKDIR /app
COPY . /app

RUN /root/.pyenv/versions/3.11.12/bin/pip \
        install --break-system-packages -r /app/requirements.txt

# New: make Python the entry-point
ENTRYPOINT ["/root/.pyenv/versions/3.11.12/bin/python"]
CMD ["run_pipeline.py"]