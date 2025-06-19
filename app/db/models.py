from sqlalchemy import Column, Integer, Text, TIMESTAMP, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Page(Base):
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    last_modified_date = Column(TIMESTAMP, nullable=False)

    # Relationship to links where this page is the source
    out_links = relationship(
        "Link",
        back_populates="source_page",
        foreign_keys="Link.source_page_id",
        cascade="all, delete-orphan",
        lazy="joined"
    )
    
    # Optional: links where this page is the target
    in_links = relationship(
        "Link",
        back_populates="target_page",
        foreign_keys="Link.target_page_id",
        cascade="all, delete-orphan",
        lazy="joined"
    )


class Category(Base):
    __tablename__ = "categories"
    
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), primary_key=True)
    category_name = Column(Text, nullable=False)

    __table_args__ = (
        Index("idx_category_name", "category_name"),
    )



class Link(Base):
    __tablename__ = "links"
    
    source_page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), primary_key=True)
    target_page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), primary_key=True)
    link_index = Column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_links_source", "source_page_id"),
        Index("idx_links_target", "target_page_id"),
    )

    source_page = relationship(
        "Page",
        foreign_keys=[source_page_id],
        back_populates="out_links"
    )

    target_page = relationship(
        "Page",
        foreign_keys=[target_page_id],
        back_populates="in_links"
    )
