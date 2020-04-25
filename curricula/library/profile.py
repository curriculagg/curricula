import linecache
import tracemalloc


def summarize(snapshot: tracemalloc.Snapshot, key_type: str, limit: int):
    """Summarize snapshot in console."""

    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_statistics = snapshot.statistics(key_type)

    for i, statistic in enumerate(top_statistics[:limit], 1):
        frame = statistic.traceback[0]
        print("#%s: %s:%s: %.1f KiB" % (i, frame.filename, frame.lineno, statistic.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print("    %s" % line)

    other = top_statistics[limit:]
    if other:
        size = sum(statistic.size for statistic in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(statistic.size for statistic in top_statistics)
    print("Total allocated size: %.1f KiB" % (total / 1024))
