FROM apache/airflow:2.10.5


USER airflow

# Install Python packages
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt -v


# Copy application files
COPY . .