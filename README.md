# gs-scraping/gs-scraping/README.md

# GS Scraping Project

This project is designed for web scraping using Python and Selenium with Firefox. It includes various scripts to scrape data from different sources and upload it to Supabase.

## Project Structure

```
gs-scraping
├── src
│   ├── main.py
│   ├── update_contribuyentes.py
│   ├── nominas.py
│   ├── opinion_cumplimiento.py
│   ├── runa_scraping.py
│   └── requirements.txt
├── comprobantes
├── descargas
├── .env
├── .dockerignore
├── .gitignore
├── Dockerfile
└── README.md
```

## Requirements

- Python 3.x
- Firefox
- GeckoDriver

## Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd gs-scraping
   ```

2. Install the required Python packages:
   ```
   pip install -r src/requirements.txt
   ```

3. Set up the environment variables in the `.env` file.

## Docker Setup

To run the project using Docker, build the Docker image and run the container:

1. Build the Docker image:
   ```
   docker build -t gs-scraping .
   ```

2. Run the Docker container:
   ```
   docker run -v $(pwd)/comprobantes:/app/comprobantes -v $(pwd)/descargas:/app/descargas gs-scraping
   ```

## Scripts

- `main.py`: Main logic for scraping data.
- `update_contribuyentes.py`: Updates contributors' data.
- `nominas.py`: Downloads payroll data.
- `opinion_cumplimiento.py`: Manages compliance opinions.
- `runa_scraping.py`: Scrapes employee data from RunaHR.

## License

This project is licensed under the MIT License.