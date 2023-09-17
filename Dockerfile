# Use a base image with Python 3.9
FROM python:3.9-slim-buster as python-base

# Install necessary system packages
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs

# Switch to a new stage for the final image
FROM python-base as final

# Set the working directory
WORKDIR /app
RUN mkdir /app/landing-page/
# Install Node.js dependencies
COPY /landing-page/package.json /app/landing-page/package.json
RUN npm install --prefix /app/landing-page/
# Install python dependencies along with the swagger client
COPY python-client /app/python-client
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt && pip install python-client/
# Copy the project files into the container
COPY . /app
# Expose the necessary ports
RUN npm run build --prefix /app/landing-page/
# FROM nginx:alpine
# Copy the built React application from the build stage
RUN cp -r /app/landing-page/build/* /var/www/html
RUN chmod +x /app/run.sh
EXPOSE 80
EXPOSE 8501
# Define the entry point for the application
CMD ["/app/run.sh"]