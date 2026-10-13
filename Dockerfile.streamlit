FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app_ui.py .
ENV PORT=8501
CMD streamlit run app_ui.py --server.port=$PORT --server.address=0.0.0.0
