FROM python:3.9-slim-buster

RUN apt update && apt-get install -y xz-utils procps wget && apt clean && rm -rf /var/cache/* \
    && pip install -i https://pypi.tuna.tsinghua.edu.cn/simple requests pyyaml

COPY .config /root/.config
COPY build.py startup.py /root/

WORKDIR /root/

RUN python3 build.py

#CMD ["bash"]
#CMD ["/usr/local/bin/python", "/root/startup.py"]
CMD ["python3", "startup.py"]