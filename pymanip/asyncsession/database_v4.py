"""AsyncSession Database Schema
===============================

New in version 4:

- New metadata table for text parameters;

- Add index for timestamp and name in Log table;

- Add index for timestamp and name in Dataset table;

- Add explicit rowid column as primary key for Log and Dataset tables (this was already automatically added
  by SQLite). Remove the synthetic compound primary key.

"""

from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    Text,
    Integer,
    Double,
    BLOB,
    UniqueConstraint,
    ForeignKey,
    inspect,
)

database_version = 4.0
Base = declarative_base()


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
    timestamp = Column(Integer, index=True)
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


def create_tables(engine):
    new = False
    if not inspect(engine).has_table("log_names"):
        LogName.metadata.create_all(engine)
        new = True
    if not inspect(engine).has_table("log"):
        Log.metadata.create_all(engine)
        new = True
    if not inspect(engine).has_table("dataset_names"):
        DatasetName.metadata.create_all(engine)
        new = True
    if not inspect(engine).has_table("dataset"):
        Dataset.metadata.create_all(engine)
        new = True
    if not inspect(engine).has_table("parameters"):
        Parameter.metadata.create_all(engine)
        new = True
    if not inspect(engine).has_table("metadata"):
        Metadata.metadata.create_all(engine)
        new = True
    return new


def copy_table(input_session, output_session, table):
    for r in input_session.query(table).yield_per(10000):
        output_session.add(table(**r.as_dict()))
    output_session.commit()


table_list = [
    LogName,
    Log,
    DatasetName,
    Dataset,
    Parameter,
    Metadata,
]