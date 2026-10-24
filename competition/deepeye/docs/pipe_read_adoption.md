# Pipe-read adoption

The inactive native pipe-read leaf distinguishes an open empty pipe, bounded data
and broken-pipe EOF without conflating EOF with temporary absence of data.
It validates exact argument types/ranges before lazy native initialization,
peeks once and reads at most 8192 bytes once. Other errors propagate; unexpected
zero, oversized or non-bytes results refuse. It never retries, waits for further
data, writes, closes endpoints or makes lifecycle/authority decisions.

Main accepted these exact three files after independent source/native review and
artifact verification. Author 12 methods and independent two native controls have
their separate scopes and preserved failures in the
[evidence archive](../evidence/system/a-pipe-read-20261021/README.md).
No production consumer was added, and existing cleanup behavior is unchanged.

A future owner must provide sole-reader discipline, actual original endpoint
ownership and EOF retirement before admission. The helper does not supply model
initialization, completion identity, source freshness, clock/slot provenance or a
hard hang bound. Real completion IPC and both full H12 chains remain incomplete;
R03 and all29 formal cards remain not_run. H01-H15 are unchanged.
