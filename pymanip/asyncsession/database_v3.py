"""AsyncSession Database Schema
===============================

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

database_version = 3.1
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

    timestamp = Column(Integer)
    name = Column(Text, ForeignKey(LogName.name))
    value = Column(Double)

    __mapper_args__ = {
        "primary_key": [name, timestamp],
    }

    def as_dict(self):
        return {
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

    timestamp = Column(Integer)
    name = Column(Text, ForeignKey(DatasetName.name))
    data = Column(BLOB)

    __mapper_args__ = {
        "primary_key": [name, timestamp],
    }

    def as_dict(self):
        return {
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
]
