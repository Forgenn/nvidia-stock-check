FROM python:3.12-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml main.py uv.lock ./

# Install dependencies using uv
RUN uv venv
RUN uv pip install -e .

# Run the stock checker
CMD ["uv", "run", "main.py"]