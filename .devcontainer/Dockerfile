FROM eclipse-temurin:21-jdk

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        git curl ca-certificates sudo gnupg \
        nodejs npm ripgrep jq \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code

# eclipse-temurin:21-jdk already has a user with UID 1000 — remove it to free the UID for our 'dev' user.
RUN if id -u 1000 >/dev/null 2>&1; then \
        existing_user="$(id -un 1000)"; \
        userdel -r "$existing_user" 2>/dev/null || userdel "$existing_user"; \
    fi \
    && useradd --uid 1000 -m -s /bin/bash dev \
    && echo "dev ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/dev

USER dev
WORKDIR /workspace

CMD ["sleep", "infinity"]