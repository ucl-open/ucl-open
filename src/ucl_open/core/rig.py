from pydantic import Field

from swc.aeon.schema import BaseSchema


class Rig(BaseSchema):
    root_path: str = Field(description="The root path on which to log all data.")
