"""

Async Driver extension for the Newport Model XPS-RL Motion controller

"""

import asyncio
import fluidlab.instruments.motor_controller.newport_xps_rl as fl_np

__all__ = ["AsyncNewportXpsRL"]


class AsyncNewportXpsRL(fl_np.NewportXpsRL):
    async def aopen(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.ip_address, self.port
        )

    async def aclose(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def __aenter__(self):
        await self.aopen()
        return self

    async def __aexit__(self, type_, value, cb):
        await self.aclose()

    async def aquery(self, command_str):
        if isinstance(command_str, str):
            command_str = command_str.encode("ascii")
        self.writer.write(command_str)
        await self.writer.drain()
        chunks = []
        while True:
            chunk = await self.reader.read(1024)
            if len(chunk) > 0:
                chunks.append(chunk)
            if len(chunks) < 1024:
                break
        return self._parse_chunks(chunks)

    async def FirmwareVersionGet(self):
        status, response = await self.aquery("FirmwareVersionGet(char *)")
        if status != 0:
            raise fl_np.NewportXpsRLError(status, response)
        return response

    async def ControllerStatusGet(self):
        status, response = await self.aquery("ControllerStatusGet(int *)")
        if status != 0:
            raise fl_np.NewportXpsRLError(status, response)
        return fl_np.NewportXpsRLControllerStatus(int(response))

    async def Login(self, username, password):
        status, response = await self.aquery(f"Login({username}, {password}")
        if status != 0:
            raise fl_np.NewportXpsRLError(status, response)

    async def GroupPositionSetpointGet(self, groupname="Group1.Pos"):
        """
        The SetpointPosition is the profiler position. This is the position where the
        positioner should be according to the ideal theoretical motion profile.
        """

        status, response = await self.aquery(
            f"GroupPositionSetpointGet({groupname}, double *)"
        )
        if status != 0:
            raise fl_np.NewportXpsRLError(status, response)
        return float(response)

    async def GroupPositionCurrentGet(self, groupname="Group1.Pos"):
        """
        The CurrentPosition is the encoder position of the stage after mapping corrections are
        applied. This is the actual position of the positioner at this moment of the query.
        """

        status, response = await self.aquery(
            f"GroupPositionCurrentGet({groupname}, double *)"
        )
        if status != 0:
            raise fl_np.NewportXpsRLError(status, response)
        return float(response)

    async def GroupPositionTargetGet(self, groupname="Group1.Pos"):
        """
        The TargetPosition is the final target position commanded by the user.
        """

        status, response = await self.aquery(
            f"GroupPositionTargetGet({groupname}, double *)"
        )
        if status != 0:
            raise fl_np.NewportXpsRLError(status, response)
        return float(response)

    async def GroupMoveAbsolute(self, groupname="Group1.Pos", target=250.0):
        """
        Initiates an absolute move for a positioner or a group.
        """

        status, response = await self.aquery(
            "GroupMoveAbsolute({:}, {:.2f})".format(groupname, float(target))
        )
        if status != 0:
            raise fl_np.NewportXpsRLError(status, response)
