class Messages:
  class Database:
    FETCH_ERROR = "Database fetching error"
    def DATABASE_DELETE_ERROR(entity):
      return f"Database error while deleting {entity}"
    def CREATE_ERROR(entity: str):
      return f"Database error while creating {entity}"
    def NOT_FOUND(entity: str):
      return f"{entity} not found"
    def NOT_FOUND_BY_ID(entity: str, id: int | str):
      return f"{entity} with ID {id} not found"
  
  def ALREADY_EXISTS(entity: str):
    return f"{entity} is already exists"
