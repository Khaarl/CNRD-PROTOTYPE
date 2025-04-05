    def to_dict(self):
        """Convert program data to dictionary for saving"""
        return {
            "id": self.id.lower(),
            "name": self.name,
            "power": self.power,
            "accuracy": self.accuracy,
            "type": self.type,
            "effect": self.effect,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a Program instance from saved dictionary data"""
        return cls(
            id=data.get("id", "unknown_program"),
            name=data.get("name", "Unknown Program"),
            power=data.get("power", 0),
            accuracy=data.get("accuracy", 100),
            type=data.get("type", "NORMAL"),
            effect=data.get("effect", "none"),
            description=data.get("description", "No description available.")
        )