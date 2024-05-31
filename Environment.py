from llvmlite import ir


class Environment:
    def __init__(self, records: dict[str, tuple[ir.Value, ir.Type]], parent=None, name="Global") -> None:
        self.records = records # name to (pointer, variable ir type)
        self.parent = parent
        self.name = name

    def define(self, name: str, value: ir.Value, type: ir.Type) -> None:
        self.records[name] = (value, type)
    
    def lookup(self, name: str) -> tuple[ir.Value, ir.Type] | None:
        if name in self.records: return self.records[name]
        elif self.parent: return self.parent.lookup(name)
        return None
