# Use an official Python runtime as the parent image
FROM --platform=linux/amd64 python:3.11.5-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install dependencies
# Copy only the requirements.txt first to leverage Docker cache
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code after building dependencies
COPY . .

# Expose the port the app runs on
EXPOSE 4444

# Run the script when the container launches
# Make sure to remove --reload for production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4444"]