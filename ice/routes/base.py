from pydantic import BaseModel


def camel_cased(string: str) -> str:
    return "".join(w.capitalize() if i else w for i, w in enumerate(string.split("_")))


class RouteModel(BaseModel):
    class Config:
        alias_generator = camel_cased
        allow_population_by_field_name = True
