def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """
    Convert between common units.
    Supported types: Length (m, km, mi, ft), Weight (kg, lb), Temp (c, f).
    """
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    # Length conversions (base: meter)
    length_factors = {
        "m": 1,
        "km": 1000,
        "mi": 1609.34,
        "ft": 0.3048,
        "in": 0.0254,
        "cm": 0.01
    }
    
    # Weight conversions (base: kg)
    weight_factors = {
        "kg": 1,
        "lb": 0.453592,
        "g": 0.001,
        "oz": 0.0283495
    }
    
    try:
        # Temperature
        if from_unit in ["c", "celsius"] and to_unit in ["f", "fahrenheit"]:
            return f"{value} C = {(value * 9/5) + 32:.2f} F"
        if from_unit in ["f", "fahrenheit"] and to_unit in ["c", "celsius"]:
            return f"{value} F = {(value - 32) * 5/9:.2f} C"
            
        # Length
        if from_unit in length_factors and to_unit in length_factors:
            base_value = value * length_factors[from_unit]
            converted = base_value / length_factors[to_unit]
            return f"{value} {from_unit} = {converted:.4f} {to_unit}"
            
        # Weight
        if from_unit in weight_factors and to_unit in weight_factors:
            base_value = value * weight_factors[from_unit]
            converted = base_value / weight_factors[to_unit]
            return f"{value} {from_unit} = {converted:.4f} {to_unit}"
            
        return f"Error: Conversion from {from_unit} to {to_unit} not supported."
        
    except Exception as e:
        return f"Error converting: {str(e)}"
