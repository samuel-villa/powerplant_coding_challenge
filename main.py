from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI()


class PayLoad(BaseModel):
    """
    Represents the payload structure expected in the POST request body.
    """
    load: float
    fuels: dict
    powerplants: list


class PowerPlant:
    """
    Represents a power plant with its attributes provided within input data 
    plus added methods that allows to classify the object.
    """
    def __init__(self, data):
        self.name = data['name']
        self.type = data['type']
        self.efficiency = data['efficiency']
        self.pmin = data['pmin']
        self.pmax = data['pmax']
        self.min_cost = 0
        self.max_cost = 0
        self.unit_cost = 0
        self.fuel = self.determine_fuel()
        self.is_wind = True if self.type == 'windturbine' else False
        self.max_production = 0
        self.to_produce = 0

    def determine_fuel(self):
        """
        :returns: [str] The type of fuel used by the power plant.
        """
        if self.type:
            if self.type == 'gasfired':
                self.fuel = 'gas(euro/MWh)'
            elif self.type == 'turbojet':
                self.fuel =  'kerosine(euro/MWh)'
            elif self.type == 'windturbine':
                self.fuel = 'wind(%)'
            return self.fuel
        else:
            raise ValueError(f"No type defined for powerplant '{self.name}'")
        
    def get_unit_price_cost(self, fuel_cost_per_mwh):
        """
        :fuel_cost_per_mwh: [float] The cost of fuel per MWh.
        :return: [float] Cost needed to produce 1 unit of power
        """
        if not self.is_wind:
            if self.efficiency <= 0 or self.efficiency > 1:
                raise ValueError("Efficiency should be between 0 and 1")
            if fuel_cost_per_mwh <= 0:
                raise ValueError("Fuel cost should be greater than 0")
            return float("{:.1f}".format(fuel_cost_per_mwh / self.efficiency))
        else:
            return 0
        

def store_powerplants(data):
    # creating a list of powerplant objects
    powerplants = []
    for pp in data.powerplants:
        pp_data = {
        "name": pp['name'],
        "type": pp['type'],
        "efficiency": pp['efficiency'],
        "pmin": pp['pmin'],
        "pmax": pp['pmax'],
        }
        p = PowerPlant(pp_data)
        powerplants.append(p)
    return powerplants

def produce_energy(data, powerplants):
    # producing requested load
    production = 0
    remaining_to_produce = data.load
    while remaining_to_produce > 0:
        for pp in powerplants:
            if pp.max_production <= remaining_to_produce:
                pp.to_produce = pp.max_production
                production += pp.to_produce
                remaining_to_produce -= pp.to_produce
            elif pp.max_production > remaining_to_produce:
                pp.to_produce = remaining_to_produce
                remaining_to_produce -= pp.to_produce


@app.post("/productionplan")
async def production_plan(data: PayLoad):

    response = []

    # check data
    if not data.load or data.load < 0:
        raise HTTPException(status_code=400, detail="'load' not provided or incorrect. It must be greater than 0.")
    if data.fuels:
        if data.fuels['wind(%)'] and data.fuels['wind(%)'] >= 0:
            wind = data.fuels['wind(%)']
        else:
            raise HTTPException(status_code=400, detail="'wind' not provided or incorrect. It must be greater than 0.")
    else:
        raise HTTPException(status_code=400, detail="'fuels' not provided or incorrect.")
    
    if data.powerplants:
        # creating a list of powerplant objects
        powerplants = store_powerplants(data)

        # calculating powerplants data so to allow the object classification/ordering
        for pp in powerplants:
            if data.fuels[pp.fuel]:
                pp.unit_cost = pp.get_unit_price_cost(data.fuels[pp.fuel])
                pp.min_cost = float("{:.1f}".format(pp.unit_cost * pp.pmin))
                pp.max_cost = float("{:.1f}".format(pp.unit_cost * pp.pmax))
                pp.max_production = float("{:.1f}".format(pp.pmax * (wind / 100))) if pp.is_wind else float("{:.1f}".format(pp.pmax))
            else:
                raise HTTPException(status_code=400, detail=f"'{data.fuels[pp.fuel]}' not provided or incorrect.")
            
        # ordering powerplants by unit cost
        powerplants_ordered_by_unit_cost = sorted(powerplants, key=lambda x: x.unit_cost)

        produce_energy(data, powerplants_ordered_by_unit_cost)

        # generating response
        for pp in powerplants_ordered_by_unit_cost:
            response.append(
                {
                    'name': pp.name,
                    'p': pp.to_produce,
                }
            )
    else:
        raise HTTPException(status_code=400, detail="No powerplants available to produce the requested load.")

    return response


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8888)
