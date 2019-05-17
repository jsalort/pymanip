from ._lib.constants import NISysCfgLocale, NISysCfgStatus
from ._lib.session import NISysCfgInitializeSession, NISysCfgCloseHandle


class NISysCfgSession:
    def __init__(
        self,
        target="localhost",
        user=None,
        password=None,
        lang=NISysCfgLocale.Default,
        force_refresh=False,
        connect_timeout=1000,
    ):
        self.target = target
        self.user = user
        self.password = password
        self.lang = lang
        self.force_refresh = force_refresh
        self.connect_timeout = connect_timeout
        self.expertHandle = None
        self.sessionHandle = None

    def __enter__(self):
        status, expertHandle, sessionHandle = NISysCfgInitializeSession()
        if status != NISysCfgStatus.OK:
            raise RuntimeError(
                f"NISysCfgInitializeSession failed. Status: {str(status):}."
            )
        self.expertHandle = expertHandle
        self.sessionHandle = sessionHandle
        return self

    def __exit__(self, type_, value, cb):
        if self.expertHandle:
            status = NISysCfgCloseHandle(self.expertHandle)
            if status != NISysCfgStatus.OK:
                raise RuntimeError(
                    f"NISysCfgCloseHandle failed. Status: {str(status):}."
                )
        if self.sessionHandle:
            status = NISysCfgCloseHandle(self.sessionHandle)
            if status != NISysCfgStatus.OK:
                raise RuntimeError(
                    f"NISysCfgCloseHandle failed. Status: {str(status):}."
                )
