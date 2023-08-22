# Power Plant Production Planner
This FastAPI application is designed to help you plan the production of various power plants based on input data.

### Method followed
- The powerplants provided are converted as objects in order to determine other useful data using the data provided (ex: unit_cost)
- Those objects are stored in a list
- the powerplant list is ordered by powerplant unit cost (powerplant cost to produce 1 unit of power)
- In such order, the powerplants produce the requested power respecting limitations (ex: p_max)
- eventually, the response is generated.

## Launch the application

- `pip install -r requirements.txt`
- `python main.py  `

## Testing the application
The framework used for the API creation (FastAPI) provides a testing interface accessible via endpoint `/doc`.
