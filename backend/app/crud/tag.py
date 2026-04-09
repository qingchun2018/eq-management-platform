from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.tag import Tag
from ..schemas.tag import TagCreate
from ..utils.color_generator import generate_random_color


def get_tags(db: Session, project_id: int) -> List[Tag]:
    """获取某项目下全部标签"""
    return db.query(Tag).filter(Tag.project_id == project_id).order_by(Tag.id.asc()).all()


def get_tag(db: Session, tag_id: int) -> Optional[Tag]:
    return db.query(Tag).filter(Tag.id == tag_id).first()


def get_tag_by_name(db: Session, project_id: int, name: str) -> Optional[Tag]:
    return db.query(Tag).filter(Tag.project_id == project_id, Tag.name == name).first()


def create_tag(db: Session, tag: TagCreate) -> Tag:
    color = tag.color if tag.color else generate_random_color()
    db_tag = Tag(project_id=tag.project_id, name=tag.name, color=color)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


def update_tag(db: Session, tag_id: int, name: str | None, color: str | None) -> Tag | None:
    tag = get_tag(db, tag_id)
    if not tag:
        return None
    if name is not None:
        tag.name = name
    if color is not None:
        tag.color = color
    db.commit()
    db.refresh(tag)
    return tag


def delete_tag(db: Session, tag_id: int) -> bool:
    tag = get_tag(db, tag_id)
    if not tag:
        return False

    db.delete(tag)
    db.commit()
    return True
