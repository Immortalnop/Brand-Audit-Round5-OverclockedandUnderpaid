"""Deadline-bounded IPC and cancellation; spawn avoids inherited thread locks."""
import multiprocessing
import os
import signal
import time
import threading
import queue
from dataclasses import dataclass
from typing import Any, Optional

@dataclass(frozen=True)
class IsolatedResult:
    ok: bool
    value: Any
    timed_out: bool
    error: Optional[str]
    cancelled: bool = False


def _get_context():
    return multiprocessing.get_context('spawn')


def _double(x):return x*2

def _hang_forever():
    while True:time.sleep(1)

def _raises():raise ValueError('child blew up')


def _child_entry(target,args,kwargs,pipe):
    if os.name=='posix' and not os.environ.get('_BRAND_AUDIT_CHILD_GROUP'):
        os.setsid();os.environ['_BRAND_AUDIT_CHILD_GROUP']='1'
    try:pipe.send(('ok',target(*args,**kwargs)))
    except Exception as exc:pipe.send(('error',repr(exc)))
    finally:pipe.close()


def _stop(proc,grace,owns_group):
    if proc.pid is None:return
    def stop_group(sig):
        if owns_group:
            try:os.killpg(proc.pid,sig);return True
            except ProcessLookupError:pass
        return False
    if not stop_group(signal.SIGTERM) and proc.is_alive():proc.terminate()
    proc.join(grace)
    # Kill the group even if its leader exited but a descendant ignored SIGTERM.
    if os.name=='posix':stop_group(signal.SIGKILL)
    if proc.is_alive():proc.kill()
    proc.join(grace)


def run_isolated(target,args=(),kwargs=None,timeout_s=30.,kill_grace_s=.25,on_wait=None):
    ctx=_get_context();recv,send=ctx.Pipe(duplex=False)
    proc=ctx.Process(target=_child_entry,args=(target,args,kwargs or {},send),daemon=False)
    mailbox=queue.Queue(maxsize=1)
    owns_group=os.name=='posix' and not os.environ.get('_BRAND_AUDIT_CHILD_GROUP')
    started=time.monotonic()
    def receive():
        try:mailbox.put(recv.recv())
        except (EOFError,OSError) as exc:mailbox.put(('error','worker IPC closed: '+str(exc)))
    try:
        proc.start();send.close()
        # recv() may block on a partial frame. Only a daemon reader may wait there.
        reader=threading.Thread(target=receive,daemon=True);reader.start()
        next_update=started+5
        while True:
            remaining=timeout_s-(time.monotonic()-started)
            if remaining<=0:return IsolatedResult(False,None,True,f'exceeded {timeout_s}s and was stopped')
            try:
                status,value=mailbox.get(timeout=min(.1,remaining))
                return IsolatedResult(status=='ok',value if status=='ok' else None,False,value if status!='ok' else None)
            except queue.Empty:
                if on_wait and time.monotonic()>=next_update:
                    on_wait(time.monotonic()-started);next_update=time.monotonic()+5
    except KeyboardInterrupt:
        return IsolatedResult(False,None,False,'Audit cancelled by user; worker stopped.',True)
    except Exception as exc:
        return IsolatedResult(False,None,False,'Worker launch or IPC failed: '+repr(exc))
    finally:
        send.close()
        _stop(proc,kill_grace_s,owns_group)
        recv.close()
        if proc.pid is not None and not proc.is_alive():proc.close()
