from goofi.data import DataType, Data
from goofi.node import Node
from goofi.params import StringParam

class TableSelectString(Node):
    def config_input_slots():
        return {"input_table": DataType.TABLE}

    def config_output_slots():
        return {"output_string": DataType.STRING}

    def config_params():
        return {
            "selection": {"key": StringParam("default_key")},
            "common": {"autotrigger": True},
        }

    def process(self, input_table: Data):
        if input_table is None or input_table.data is None:
            raise ValueError("Input table is None.")
        
        # Retrieve the selected key
        selected_key = self.params["selection"]["key"].value
        
        if selected_key not in input_table.data:
            raise KeyError(f"{selected_key} not found in the input table.")
        
        selected_value = input_table.data[selected_key]
        #print(selected_value)
        #print(type(selected_value))
        if selected_value.dtype!=DataType.STRING:
            raise ValueError(f"The value for {selected_key} is not a string.")
        
        return {"output_string": (selected_value.data, input_table.meta)}
