"""

Asynchroneous extension to fluidlab iec60488

"""

import fluidlab.instruments.iec60488 as fl_iec60488
from pymanip.aioinstruments.aiofeatures import (
    AsyncWriteCommand,
    AsyncQueryCommand,
    AsyncRegisterValue,
)
from pymanip.aioinstruments.aiodrivers import AsyncDriver


class AsyncIEC60488(AsyncDriver, fl_iec60488.IEC60488):
    async def __aenter__(self):
        await super().__aenter__()
        identification = await self.aquery_identification()

        if isinstance(identification, str):
            identification = identification.strip()

        print(f"Initialization driver for device: {identification}")

        return self

    async def aquery_event_status_register(self):
        number = await self.aquery_esr()
        return self.status_enable_register.compute_dict_from_number(number)

    async def aquery_status_register(self):
        number = await self.aquery_stb()
        return self.status_enable_register.compute_dict_from_number(number)


afeatures = [
    # Reporting Commands
    AsyncWriteCommand("aclear_status", "Clears the data status structure", "*CLS"),
    AsyncRegisterValue(
        "event_status_enable_register",
        doc=(
            """Event status enable register

Used in the status and events reporting system.
"""
        ),
        command_set="*ESE",
        keys=fl_iec60488.EVENT_STATUS_BYTES,
    ),
    AsyncQueryCommand("aquery_esr", "Query the event status register", "*ESR?"),
    AsyncRegisterValue(
        "status_enable_register",
        doc=(
            """Status enable register

Used in the status reporting system.
"""
        ),
        command_set="*SRE",
        keys=fl_iec60488.EVENT_STATUS_BYTES,
    ),
    AsyncQueryCommand("aquery_stb", "Query the status register", "*STB?"),
    # Internal operation commands
    AsyncQueryCommand("aquery_identification", "Identification query", "*IDN?"),
    AsyncWriteCommand("areset_device", "Perform a device reset", "*RST"),
    AsyncQueryCommand("aperform_internal_test", "Perform internal self-test", "*TST?"),
    # Synchronization commands
    AsyncWriteCommand(
        "await_till_completion_of_operations",
        'Return "1" when all operation are completed',
        "*OPC",
    ),
    AsyncQueryCommand(
        "aget_operation_complete_flag", "Get operation complete flag", "*OPC?"
    ),
    AsyncQueryCommand("await", "Wait to continue", "*WAI"),
]

AsyncIEC60488._build_class_with_features(afeatures)
