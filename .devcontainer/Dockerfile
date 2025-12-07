FROM registry.gitlab.com/ska-telescope/ska-python-uv/ska-build-python-uv:0.2.0

ARG USERNAME=jirachecker
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -ms /bin/bash $USERNAME

ENV LC_ALL=C

USER $USERNAME
