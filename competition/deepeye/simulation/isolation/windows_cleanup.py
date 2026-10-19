"""Checked cleanup on exact owned references; API is injectable for offline tests."""
from .resource_cleanup import Outcome
from .owned_resources import error_info


class WindowsCleanupBackend:
    def __init__(self, api, owner):
        self.api, self.owner = api, owner
        self.profile_delete_hresult = None
        self.profile_absence = None
        self.terminated = False
        self.exit_codes = {}
        owner.bind_releaser(self.release_reference)

    def reference(self, resource):
        ref = resource.identity
        if not self.owner.owns(ref) or ref.ambiguous:
            raise ValueError('resource is not held by this owner')
        return ref

    def terminate(self, resource):
        ref = self.reference(resource)
        state = self.api.Wait(ref.native, 0)
        if type(state) is not int:
            raise OSError('initial terminal readback requires an int DWORD')
        if state == 0:
            return Outcome.CONFIRMED
        if state != 258:
            raise OSError('initial terminal readback failed: ' + str(state))
        self.api.check(self.api.TerminateProcess(ref.native, 0xdead), 'TerminateProcess owned fixture')
        self.terminated = True
        return Outcome.CONFIRMED

    def wait_terminal(self, resource):
        ref = self.reference(resource)
        state = self.api.Wait(ref.native, 5000)
        if type(state) is not int:
            raise OSError('terminal readback requires an int DWORD')
        if state not in (0, 258):
            raise OSError('terminal readback failed: ' + str(state))
        ref.terminal_confirmed = state == 0
        if ref.terminal_confirmed and callable(getattr(self.api, 'exit_code', None)):
            try:
                self.exit_codes[ref.resource_id] = self.api.exit_code(ref.native)
            except BaseException as error:
                self.owner.errors.append(error_info('exit_code_readback', error, ref.resource_id))
        return ref.terminal_confirmed

    def close(self, resource):
        return self.owner.release_once(self.reference(resource))

    def remove_profile(self, resource):
        return self.owner.release_once(self.reference(resource))

    def release_reference(self, ref):
        if not self.owner.owns(ref) or ref.ambiguous:
            raise ValueError('foreign reference')
        if ref.kind == 'process' and not ref.terminal_confirmed:
            raise RuntimeError('process reference needed for unconfirmed terminal recovery')
        if ref.recovery and any(r.kind == 'process' and not r.terminal_confirmed for r in self.owner.references):
            raise RuntimeError('control reference needed for unconfirmed terminal recovery')
        if ref.release == 'kernel':
            self.api.check(self.api.CloseHandle(ref.native), 'CloseHandle owned ' + ref.label)
        elif ref.release == 'sid':
            if any(other.release == 'attributes' and other.outcome is not Outcome.CONFIRMED
                   for other in self.owner.references):
                return Outcome.UNKNOWN  # Attribute values may still reference SID storage.
            if self.api.FreeSid(ref.native):
                raise OSError('FreeSid returned an unresolved allocation')
        elif ref.release == 'local':
            if self.api.LocalFree(ref.native):
                raise OSError('LocalFree returned an unresolved allocation')
        elif ref.release == 'cotask':
            self.api.CoTaskMemFree(ref.native)  # Documented void-return helper contract.
        elif ref.release == 'attributes':
            self.api.DeleteAttributes(ref.native)  # Documented void-return helper contract.
        elif ref.release == 'profile':
            if self.owner.profile_path is None:
                return Outcome.UNKNOWN
            if any(other.profile_id == ref.resource_id and other.outcome is not Outcome.CONFIRMED
                   for other in self.owner.references):
                return Outcome.UNKNOWN
            hr = self.api.DeleteProfile(ref.native)
            self.profile_delete_hresult = hr
            if hr < 0:
                return Outcome.FAILED
            self.profile_absence = self.api.profile_absent(self.owner.profile_path)
            return Outcome.CONFIRMED if self.profile_absence is True else Outcome.UNKNOWN
        else:
            raise ValueError('unsupported owned release kind')
        return Outcome.CONFIRMED
