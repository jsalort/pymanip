"""AsyncSession Database Schema
===============================

New in version 4:

- New metadata table for text parameters;

- Add index for timestamp and name in Log table;

- Add index for timestamp and name in Dataset table;

- Add explicit rowid column as primary key for Log and Dataset tables (this was already automatically added
  by SQLite). Remove the synthetic compound primary key.

"""

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import (
    Column,
    Text,
    Integer,
    Double,
    BLOB,
    UniqueConstraint,
    ForeignKey,
    inspect,
    select,
)

database_version = 4.1


class Base(AsyncAttrs, DeclarativeBase):
    pass


class LogName(Base):
    __tablename__ = "log_names"

    name = Column(Text, primary_key=True)

    def as_dict(self):
        return {
            "name": self.name,
        }


class Log(Base):
    __tablename__ = "log"

    __table_args__ = (UniqueConstraint("name", "timestamp"),)

    rowid = Column(Integer, primary_key=True)
    timestamp = Column(Double, index=True)
    name = Column(Text, ForeignKey(LogName.name), index=True)
    value = Column(Double)

    def as_dict(self):
        return {
            "rowid": self.rowid,
            "timestamp": self.timestamp,
            "name": self.name,
            "value": self.value,
        }


class DatasetName(Base):
    __tablename__ = "dataset_names"

    name = Column(Text, primary_key=True)

    def as_dict(self):
        return {
            "name": self.name,
        }


class Dataset(Base):
    __tablename__ = "dataset"

    __table_args__ = (UniqueConstraint("name", "timestamp"),)

    rowid = Column(Integer, primary_key=True)
    timestamp = Column(Integer, index=True)
    name = Column(Text, ForeignKey(DatasetName.name), index=True)
    data = Column(BLOB)

    def as_dict(self):
        return {
            "rowid": self.rowid,
            "timestamp": self.timestamp,
            "name": self.name,
            "data": self.data,
        }


class Parameter(Base):
    __tablename__ = "parameters"

    name = Column(Text, primary_key=True)
    value = Column(Double)

    def as_dict(self):
        return {
            "name": self.name,
            "value": self.value,
        }


class Metadata(Base):
    __tablename__ = "metadata"

    name = Column(Text, primary_key=True)
    value = Column(Text)

    def as_dict(self):
        return {
            "name": self.name,
            "value": self.value,
        }


class Figure(Base):
    __tablename__ = "figure"

    fignum = Column(Integer, primary_key=True)
    maxvalues = Column(Integer)
    yscale = Column(Text)
    ymin = Column(Double)
    ymax = Column(Double)

    def as_dict(self):
        return {
            "fignum": self.fignum,
            "maxvalues": self.maxvalues,
            "yscale": self.yscale,
            "ymin": self.ymin,
            "ymax": self.ymax,
        }


class FigureVariable(Base):
    __tablename__ = "figure_variable"

    varnum = Column(Integer, primary_key=True)
    fignum = Column(Integer, ForeignKey(Figure.fignum), index=True)
    name = Column(Text, ForeignKey(LogName.name))

    def as_dict(self):
        return {
            "varnum": self.varnum,
            "fignum": self.fignum,
            "name": self.name,
        }


def create_tables(conn):
    """At this time, sqlalchemy does not support async inspection.
    So, use:
    ```python
    conn.run_sync(create_tables)
    ```
    """
    new = False
    if not inspect(conn).has_table("log_names"):
        LogName.metadata.create_all(conn)
        new = True
    if not inspect(conn).has_table("log"):
        Log.metadata.create_all(conn)
        new = True
    if not inspect(conn).has_table("dataset_names"):
        DatasetName.metadata.create_all(conn)
        new = True
    if not inspect(conn).has_table("dataset"):
        Dataset.metadata.create_all(conn)
        new = True
    if not inspect(conn).has_table("parameters"):
        Parameter.metadata.create_all(conn)
        new = True
    if not inspect(conn).has_table("metadata"):
        Metadata.metadata.create_all(conn)
        new = True
    if not inspect(conn).has_table("figure"):
        Figure.metadata.create_all(conn)
        new = True
    if not inspect(conn).has_table("figure_variable"):
        FigureVariable.metadata.create_all(conn)
        new = True
    return new


async def copy_table(input_session, output_session, table):
    rows = await input_session.execute(select(table))
    # count = 0
    for rr in rows.yield_per(10000):
        (r,) = rr
        new_row = table(**r.as_dict())
        output_session.add(new_row)
        # count = count + 1
    # print(" -->", table.__tablename__, ":", count, "rows")


table_list = [
    LogName,
    Log,
    DatasetName,
    Dataset,
    Parameter,
    Metadata,
    Figure,
    FigureVariable,
]
