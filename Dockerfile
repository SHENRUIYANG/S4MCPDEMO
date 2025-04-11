# Material Master Data MCP
# Version: 1.0.0
# Author: ORBIS Consulting Shanghai Co.,Ltd
# License: MIT

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "MM03_MCP.py"]
CMD ["--mode=stdio"] 