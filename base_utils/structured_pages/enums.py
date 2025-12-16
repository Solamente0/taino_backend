from base_utils.enums import TainoBaseEnum


class MenuEnums(TainoBaseEnum):
    BIG_GRID_WIDGET = "big_grid_widget"
    GRID_WIDGET = "grid_widget"
    LIST_WIDGET = "list_widget"


class MenuDirectionEnums(TainoBaseEnum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class StructuresSortMap(TainoBaseEnum):
    NEWEST = "newest"
    BEST = "best"
    MOST_VISITED = "most_visited"
    # SPECIAL = "special"

    MAP = {NEWEST: "-created_at", BEST: "-visited_times", MOST_VISITED: "-visited_times"}
