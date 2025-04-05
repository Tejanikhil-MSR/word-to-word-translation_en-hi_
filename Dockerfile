FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.10 python3-pip git wget bash && \
    ln -s /usr/bin/python3.10 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

RUN apt-get update && apt-get install -y curl

RUN pip install -r requirements.txt

RUN chmod +x ./GeneratedDatasets/extract_muse_dataset.sh

RUN ./GeneratedDatasets/extract_muse_dataset.sh

RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

CMD ["/bin/bash"]