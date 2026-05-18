from sqlalchemy import Column, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    code = Column(String(40), nullable=True)
    description = Column(String(400), nullable=True)
    # RAO-P1-017: hierarchia 3-poziomowa
    parent_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    level = Column(
        Enum("main", "sub1", "sub2", "sub3", name="category_level"),
        nullable=False,
        default="main",
        server_default="main",
    )

    # Self-referential relationship: rodzic ↔ dzieci
    parent = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children",
        lazy="selectin",
    )
    children = relationship(
        "Category",
        back_populates="parent",
        cascade="save-update",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_categories_name", "name"),
        Index("idx_categories_parent", "parent_id"),
    )
