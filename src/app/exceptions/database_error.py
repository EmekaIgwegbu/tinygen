class DatabaseError(Exception):
    def __init__(self, message, table_name):
        super().__init__(f"{table_name}: {message}")
