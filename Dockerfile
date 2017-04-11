FROM ubuntu
MAINTAINER Groot Development Team <groot-l@acm.illinois.edu>

ENV USER root
ENV RUST_VERSION=1.16.0

RUN apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    libssl-dev \
    pkg-config && \
  curl https://sh.rustup.rs -sSf | bash -s -- -y && \
  DEBIAN_FRONTEND=noninteractive apt-get remove --purge -y curl && \
  DEBIAN_FRONTEND=noninteractive apt-get autoremove -y && \
  mkdir /source
VOLUME ["/source"]
WORKDIR /source
CMD ["cargo run"]