FROM ubuntu:22.04

# Install OpenSSH server and sudo for convenience
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        openssh-server \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# Configure SSH daemon and create a non-root sudo user
RUN mkdir -p /run/sshd \
    && useradd -ms /bin/bash ubuntu \
    && echo 'ubuntu:ubuntu' | chpasswd \
    && adduser ubuntu sudo \
    && echo 'ubuntu ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/90-ubuntu \
    && sed -i 's@#PasswordAuthentication yes@PasswordAuthentication yes@' /etc/ssh/sshd_config \
    && sed -i 's@#PermitRootLogin prohibit-password@PermitRootLogin no@' /etc/ssh/sshd_config

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D", "-e"]
