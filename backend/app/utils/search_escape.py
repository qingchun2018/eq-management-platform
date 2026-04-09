"""SQL LIKE / ILIKE 用户输入中的通配符转义（PostgreSQL 默认 ESCAPE '\\'）"""


def escape_ilike_pattern(user_input: str) -> str:
    """将 % _ \\ 转义，避免用户搜索时误用通配符语义"""
    return (
        user_input.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )
