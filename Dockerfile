#base image of the container
FROM python:3.9-slim 

# Set the working directory
WORKDIR /app


# Copy the wait-for-it script
COPY wait-for-it.sh /usr/local/bin/wait-for-it
RUN chmod +x /usr/local/bin/wait-for-it

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy from cd-uwazi-api to container
COPY . .

# Expose the port Flask runs on
EXPOSE 8080

# Command to start the application
CMD ["python", "start.py"]
